import json
import os
from typing import Any, Optional

import httpx

from app.schemas.horoscope import MonthlyHoroscopeLLMResponse
from app.services.chart_engine import NatalProfile
from app.services.transit_engine import MonthlyTransitAnalysis
from app.services.upstage_schema import SchemaFlattenError, build_upstage_response_format

MONTHLY_SUPPORTED_PROVIDERS = frozenset({"xai", "upstage"})

_SCHEMA_NAME = "monthly_horoscope_enhancement"

_SYSTEM_PROMPT = (
    "당신은 점성술 계산 결과를 한국어 월간 운세 리포트로 정리하는 편집자입니다. "
    "문체는 실용적이고 차분해야 하며, 과장하거나 단정하지 않습니다. "
    "의학, 법률, 투자 확정 조언처럼 들리는 표현은 피합니다. "
    "반드시 제공된 JSON schema에 맞는 JSON만 출력합니다."
)

_DEFAULT_MODELS = {
    "upstage": "solar-pro3",
    "xai": "grok-4.20-reasoning",
}
_DEFAULT_BASE_URLS = {
    "upstage": "https://api.upstage.ai/v1",
}
# provider별 폴백 env는 반드시 provider로 스코프한다.
_PROVIDER_KEY_ENVS = {
    "upstage": "UPSTAGE_API_KEY",
    "xai": "XAI_API_KEY",
}
_PROVIDER_MODEL_ENVS = {
    "upstage": "UPSTAGE_MODEL",
    "xai": "XAI_MODEL",
}
_PROVIDER_BASE_ENVS = {
    "upstage": "UPSTAGE_API_BASE_URL",
}


class MonthlyReportClient:
    """월간 운세 리포트를 LLM으로 보강한다. xai / upstage provider를 지원한다."""

    def __init__(
        self,
        provider: str = "xai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        base_url: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
    ) -> None:
        self.provider = (provider or "xai").strip().casefold()
        self.api_key = api_key
        self.model = model or _DEFAULT_MODELS.get(self.provider, _DEFAULT_MODELS["xai"])
        self.timeout_seconds = timeout_seconds or 45.0
        self.base_url = base_url.rstrip("/") if base_url else None
        self.reasoning_effort = reasoning_effort
        self.prompt_version = "monthly-horoscope-v1"

    @classmethod
    def from_env(cls) -> "MonthlyReportClient":
        provider = os.getenv("MONTHLY_LLM_PROVIDER", "xai").strip().casefold()
        key_env = _PROVIDER_KEY_ENVS.get(provider)
        model_env = _PROVIDER_MODEL_ENVS.get(provider)
        base_env = _PROVIDER_BASE_ENVS.get(provider)
        return cls(
            provider=provider,
            api_key=os.getenv("MONTHLY_LLM_API_KEY") or (os.getenv(key_env) if key_env else None),
            model=os.getenv("MONTHLY_LLM_MODEL") or (os.getenv(model_env) if model_env else None),
            timeout_seconds=float(
                os.getenv("MONTHLY_LLM_TIMEOUT_SECONDS") or os.getenv("XAI_TIMEOUT_SECONDS") or "45"
            ),
            base_url=os.getenv("MONTHLY_LLM_BASE_URL")
            or (os.getenv(base_env) if base_env else None)
            or _DEFAULT_BASE_URLS.get(provider),
            reasoning_effort=os.getenv("UPSTAGE_REASONING_EFFORT") or None,
        )

    @property
    def enabled(self) -> bool:
        return bool(self.api_key) and self.provider in MONTHLY_SUPPORTED_PROVIDERS

    def enhance_monthly_report(
        self,
        profile: NatalProfile,
        analysis: MonthlyTransitAnalysis,
        fallback_payload: dict[str, Any],
    ) -> Optional[MonthlyHoroscopeLLMResponse]:
        if not self.enabled:
            return None

        user_payload = self._user_payload(profile, analysis, fallback_payload)
        if self.provider == "upstage":
            content = self._post_upstage(user_payload)
        else:
            content = self._post_xai(user_payload)
        if content is None:
            return None

        try:
            return MonthlyHoroscopeLLMResponse.model_validate_json(content)
        except Exception:
            return None

    def _user_payload(
        self,
        profile: NatalProfile,
        analysis: MonthlyTransitAnalysis,
        fallback_payload: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "writingRules": {
                "language": "ko",
                "style": "calm-practical",
                "keepDatesDeterministic": True,
                "doNotInventEvents": True,
            },
            "profile": {
                "sunSign": profile.sun_sign,
                "moonSign": profile.moon_sign,
                "risingSign": profile.rising_sign,
                "dominantElement": profile.dominant_element_label,
                "focusAreas": list(profile.focus_areas),
            },
            "month": {
                "year": analysis.year,
                "month": analysis.month,
                "title": analysis.title,
                "topTheme": analysis.top_theme_label,
                "intensityScore": analysis.intensity_score,
            },
            "deterministicDraft": fallback_payload,
        }

    def _post_xai(self, user_payload: dict[str, Any]) -> Optional[str]:
        request_payload = {
            "model": self.model,
            "store": False,
            "temperature": 0,
            "input": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": _SCHEMA_NAME,
                    "schema": MonthlyHoroscopeLLMResponse.model_json_schema(),
                    "strict": True,
                }
            },
        }

        try:
            response = httpx.post(
                "https://api.x.ai/v1/responses",
                headers=self._headers(),
                json=request_payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None
        return self._extract_output_text(response.json())

    def _post_upstage(self, user_payload: dict[str, Any]) -> Optional[str]:
        try:
            response_format = build_upstage_response_format(
                _SCHEMA_NAME, MonthlyHoroscopeLLMResponse.model_json_schema()
            )
        except SchemaFlattenError:
            # 스키마를 Upstage 제약에 맞출 수 없으면 json_object로 낮춘다.
            # 응답이 계약과 어긋나면 파싱이 실패해 결정론적 fallback으로 간다.
            response_format = {"type": "json_object"}

        request_payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            "response_format": response_format,
            "temperature": 0,
            "stream": False,
        }
        if self.reasoning_effort:
            request_payload["reasoning_effort"] = self.reasoning_effort

        try:
            response = httpx.post(
                f"{self._upstage_base_url()}/chat/completions",
                headers=self._headers(),
                json=request_payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None
        return self._extract_chat_completion_text(response.json())

    def _upstage_base_url(self) -> str:
        base = self.base_url or _DEFAULT_BASE_URLS["upstage"]
        return base if base.endswith("/v1") else f"{base}/v1"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _extract_output_text(self, payload: dict[str, Any]) -> Optional[str]:
        if isinstance(payload.get("output_text"), str):
            return payload["output_text"]

        for item in payload.get("output", []):
            for content in item.get("content", []):
                if isinstance(content.get("text"), str):
                    return content["text"]

        return None

    def _extract_chat_completion_text(self, payload: dict[str, Any]) -> Optional[str]:
        # message.reasoning은 최종 답이 아니므로 의도적으로 읽지 않는다.
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return None
        if isinstance(content, str):
            return content if content.strip() else None
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str) and part["text"].strip():
                    return part["text"]
        return None


class XAIService(MonthlyReportClient):
    """하위 호환 shim. 신규 코드는 MonthlyReportClient를 쓴다."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        super().__init__(
            provider="xai",
            api_key=api_key or os.getenv("XAI_API_KEY"),
            model=model or os.getenv("XAI_MODEL"),
            timeout_seconds=timeout_seconds or float(os.getenv("XAI_TIMEOUT_SECONDS", "45")),
        )
