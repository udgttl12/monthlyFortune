import json
import os
from typing import Any

import httpx

from app.schemas.horoscope import MonthlyHoroscopeLLMResponse
from app.services.chart_engine import NatalProfile
from app.services.transit_engine import MonthlyTransitAnalysis


class XAIService:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        self.model = model or os.getenv("XAI_MODEL", "grok-4.20-reasoning")
        self.timeout_seconds = timeout_seconds or float(os.getenv("XAI_TIMEOUT_SECONDS", "45"))
        self.prompt_version = "monthly-horoscope-v1"

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def enhance_monthly_report(
        self,
        profile: NatalProfile,
        analysis: MonthlyTransitAnalysis,
        fallback_payload: dict[str, Any],
    ) -> MonthlyHoroscopeLLMResponse | None:
        if not self.enabled:
            return None

        request_payload = {
            "model": self.model,
            "store": False,
            "temperature": 0,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "당신은 점성술 계산 결과를 한국어 월간 운세 리포트로 정리하는 편집자다. "
                        "문체는 실용적이고 차분해야 하며, 과장하거나 단정하지 않는다. "
                        "투자, 의학, 법률 확정 조언처럼 들리는 표현은 피한다. "
                        "반드시 제공된 JSON schema에 맞는 JSON만 출력한다."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
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
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "monthly_horoscope_enhancement",
                    "schema": MonthlyHoroscopeLLMResponse.model_json_schema(),
                    "strict": True,
                }
            },
        }

        try:
            response = httpx.post(
                "https://api.x.ai/v1/responses",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=request_payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        payload = response.json()
        content = self._extract_output_text(payload)
        if content is None:
            return None

        try:
            return MonthlyHoroscopeLLMResponse.model_validate_json(content)
        except Exception:
            return None

    def _extract_output_text(self, payload: dict[str, Any]) -> str | None:
        if isinstance(payload.get("output_text"), str):
            return payload["output_text"]

        for item in payload.get("output", []):
            for content in item.get("content", []):
                if isinstance(content.get("text"), str):
                    return content["text"]

        return None
