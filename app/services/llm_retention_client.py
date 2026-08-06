import json
import os
from typing import Any, Optional

import httpx

from app.schemas.ai_retention import (
    ActionCalendarDay,
    ActionCalendarLLMResponse,
    CoachLLMResponse,
    DailyBriefLLMResponse,
    TimingSignal,
)
from app.services.chart_engine import NatalProfile
from app.services.transit_engine import MonthlyTransitAnalysis
from app.services.upstage_schema import SchemaFlattenError, build_upstage_response_format

SUPPORTED_PROVIDERS = frozenset({"xai", "deepseek", "gemma", "upstage"})

_DEFAULT_MODELS = {
    "deepseek": "deepseek-v4-pro",
    "gemma": "unsloth/gemma-4-E2B-it-GGUF:UD-Q4_K_XL",
    "upstage": "solar-pro3",
    "xai": "grok-4.20-reasoning",
}
_DEFAULT_BASE_URLS = {
    "gemma": "https://gemma.donggyu.link",
    "upstage": "https://api.upstage.ai/v1",
}
# provider별 폴백 env는 반드시 provider로 스코프한다. 스코프하지 않으면 다른
# provider의 base_url이 잡혀 요청이 엉뚱한 호스트로 나간다.
_PROVIDER_KEY_ENVS = {
    "gemma": "GEMMA_API_KEY",
    "upstage": "UPSTAGE_API_KEY",
    "xai": "XAI_API_KEY",
}
_PROVIDER_BASE_ENVS = {
    "gemma": "GEMMA_API_BASE_URL",
    "upstage": "UPSTAGE_API_BASE_URL",
}


class LLMRetentionClient:
    def __init__(
        self,
        provider: str,
        api_key: Optional[str],
        model: str,
        timeout_seconds: float,
        base_url: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
    ) -> None:
        self.provider = provider.strip().casefold()
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url.rstrip("/") if base_url else None
        self.reasoning_effort = reasoning_effort
        self.prompt_version = "ai-retention-v1"

    @classmethod
    def from_env(cls) -> "LLMRetentionClient":
        provider = os.getenv("LLM_RETENTION_PROVIDER", "xai").strip().casefold()

        api_key = os.getenv("LLM_RETENTION_API_KEY")
        if not api_key:
            key_env = _PROVIDER_KEY_ENVS.get(provider)
            api_key = os.getenv(key_env) if key_env else None

        base_env = _PROVIDER_BASE_ENVS.get(provider)
        base_url = (
            os.getenv("LLM_RETENTION_BASE_URL")
            or (os.getenv(base_env) if base_env else None)
            or _DEFAULT_BASE_URLS.get(provider)
        )

        return cls(
            provider=provider,
            api_key=api_key,
            model=os.getenv("LLM_RETENTION_MODEL", _DEFAULT_MODELS.get(provider, _DEFAULT_MODELS["xai"])),
            timeout_seconds=float(os.getenv("LLM_RETENTION_TIMEOUT_SECONDS", "45")),
            base_url=base_url,
            reasoning_effort=os.getenv("UPSTAGE_REASONING_EFFORT") or None,
        )

    @property
    def enabled(self) -> bool:
        return bool(self.api_key) and self.provider in SUPPORTED_PROVIDERS

    def generate_action_calendar(
        self,
        profile: NatalProfile,
        analysis: MonthlyTransitAnalysis,
        signals: list[TimingSignal],
        fallback_days: list[ActionCalendarDay],
    ) -> Optional[ActionCalendarLLMResponse]:
        payload = self._generate_structured(
            schema_name="action_calendar",
            schema=ActionCalendarLLMResponse.model_json_schema(),
            system_prompt=(
                "You are a Korean astrology retention assistant. Refine deterministic timing signals into "
                "practical revisit-worthy action calendar copy. Return valid JSON only, in Korean, matching the schema."
            ),
            user_payload={
                "profile": self._profile_payload(profile),
                "month": {
                    "year": analysis.year,
                    "month": analysis.month,
                    "title": analysis.title,
                    "topTheme": analysis.top_theme_label,
                    "intensityScore": analysis.intensity_score,
                },
                "signals": [item.model_dump(mode="json", by_alias=True) for item in signals],
                "fallbackDays": [item.model_dump(mode="json", by_alias=True) for item in fallback_days],
            },
        )
        return self._parse(ActionCalendarLLMResponse, payload)

    def generate_daily_brief(
        self,
        profile: NatalProfile,
        analysis: MonthlyTransitAnalysis,
        signal: TimingSignal,
    ) -> Optional[DailyBriefLLMResponse]:
        payload = self._generate_structured(
            schema_name="daily_brief",
            schema=DailyBriefLLMResponse.model_json_schema(),
            system_prompt=(
                "You are a Korean daily astrology briefing assistant. Turn the timing signal into concise, "
                "specific, non-fatalistic guidance that makes the user want to return tomorrow. Return valid JSON only."
            ),
            user_payload={
                "profile": self._profile_payload(profile),
                "month": {"year": analysis.year, "month": analysis.month},
                "todaySignal": signal.model_dump(mode="json", by_alias=True),
            },
        )
        return self._parse(DailyBriefLLMResponse, payload)

    def answer_timing_question(
        self,
        profile: NatalProfile,
        analysis: MonthlyTransitAnalysis,
        signals: list[TimingSignal],
        question: str,
    ) -> Optional[CoachLLMResponse]:
        payload = self._generate_structured(
            schema_name="timing_coach",
            schema=CoachLLMResponse.model_json_schema(),
            system_prompt=(
                "You are a Korean decision timing coach. Answer the user's question with grounded timing guidance "
                "based on the provided signals, including recommended dates and cautions. Return valid JSON only."
            ),
            user_payload={
                "profile": self._profile_payload(profile),
                "month": {"year": analysis.year, "month": analysis.month, "topTheme": analysis.top_theme_label},
                "question": question,
                "signals": [item.model_dump(mode="json", by_alias=True) for item in signals],
            },
        )
        return self._parse(CoachLLMResponse, payload)

    def _generate_structured(
        self,
        schema_name: str,
        schema: dict[str, Any],
        system_prompt: str,
        user_payload: dict[str, Any],
    ) -> Optional[str]:
        if not self.enabled:
            return None
        if self.provider == "deepseek":
            return self._post_deepseek(system_prompt=system_prompt, user_payload=user_payload)
        if self.provider == "gemma":
            return self._post_gemma(system_prompt=system_prompt, user_payload=user_payload)
        if self.provider == "upstage":
            return self._post_upstage(
                schema_name=schema_name,
                schema=schema,
                system_prompt=system_prompt,
                user_payload=user_payload,
            )
        return self._post_xai(
            schema_name=schema_name,
            schema=schema,
            system_prompt=system_prompt,
            user_payload=user_payload,
        )

    def _post_xai(
        self,
        schema_name: str,
        schema: dict[str, Any],
        system_prompt: str,
        user_payload: dict[str, Any],
    ) -> Optional[str]:
        request_payload = {
            "model": self.model,
            "store": False,
            "temperature": 0,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
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
        return self._extract_xai_text(response.json())

    def _post_deepseek(self, system_prompt: str, user_payload: dict[str, Any]) -> Optional[str]:
        request_payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "stream": False,
        }
        try:
            response = httpx.post(
                "https://api.deepseek.com/chat/completions",
                headers=self._headers(),
                json=request_payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None
        return self._extract_deepseek_text(response.json())

    def _post_gemma(self, system_prompt: str, user_payload: dict[str, Any]) -> Optional[str]:
        if not self.base_url:
            return None
        request_payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            "temperature": 0,
            "max_tokens": 2048,
            "stream": False,
        }
        try:
            response = httpx.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self._headers(),
                json=request_payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None
        return self._extract_deepseek_text(response.json())

    def _post_upstage(
        self,
        schema_name: str,
        schema: dict[str, Any],
        system_prompt: str,
        user_payload: dict[str, Any],
    ) -> Optional[str]:
        try:
            response_format = build_upstage_response_format(schema_name, schema)
        except SchemaFlattenError:
            # 스키마를 Upstage 제약에 맞출 수 없으면 json_object로 낮춘다.
            # 응답이 계약과 어긋나면 _parse가 None을 돌려 결정론적 fallback으로 간다.
            response_format = {"type": "json_object"}

        request_payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
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
        return self._extract_upstage_text(response.json())

    def _upstage_base_url(self) -> str:
        base = self.base_url or _DEFAULT_BASE_URLS["upstage"]
        return base if base.endswith("/v1") else f"{base}/v1"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _extract_xai_text(self, payload: dict[str, Any]) -> Optional[str]:
        if isinstance(payload.get("output_text"), str):
            return payload["output_text"]
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if isinstance(content.get("text"), str):
                    return content["text"]
        return None

    def _extract_deepseek_text(self, payload: dict[str, Any]) -> Optional[str]:
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return None
        return content if isinstance(content, str) and content.strip() else None

    def _extract_upstage_text(self, payload: dict[str, Any]) -> Optional[str]:
        text = self._extract_deepseek_text(payload)
        if text is not None:
            return text
        # solar-pro3는 content를 파트 배열로 돌려줄 수 있다.
        # message.reasoning은 최종 답이 아니므로 의도적으로 읽지 않는다.
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return None
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str) and part["text"].strip():
                    return part["text"]
        return None

    def _parse(self, model_class, payload: Optional[str]):
        if payload is None:
            return None
        try:
            return model_class.model_validate_json(payload)
        except Exception:
            return None

    def _profile_payload(self, profile: NatalProfile) -> dict[str, Any]:
        return {
            "sunSign": profile.sun_sign,
            "moonSign": profile.moon_sign,
            "risingSign": profile.rising_sign,
            "dominantElement": profile.dominant_element_label,
            "focusAreas": list(profile.focus_areas),
        }
