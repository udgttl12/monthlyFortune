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


class LLMRetentionClient:
    def __init__(
        self,
        provider: str,
        api_key: Optional[str],
        model: str,
        timeout_seconds: float,
    ) -> None:
        self.provider = provider.strip().casefold()
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.prompt_version = "ai-retention-v1"

    @classmethod
    def from_env(cls) -> "LLMRetentionClient":
        provider = os.getenv("LLM_RETENTION_PROVIDER", "xai").strip().casefold()
        default_model = "deepseek-v4-pro" if provider == "deepseek" else "grok-4.20-reasoning"
        api_key = os.getenv("LLM_RETENTION_API_KEY")
        if not api_key and provider == "xai":
            api_key = os.getenv("XAI_API_KEY")
        return cls(
            provider=provider,
            api_key=api_key,
            model=os.getenv("LLM_RETENTION_MODEL", default_model),
            timeout_seconds=float(os.getenv("LLM_RETENTION_TIMEOUT_SECONDS", "45")),
        )

    @property
    def enabled(self) -> bool:
        return bool(self.api_key) and self.provider in {"xai", "deepseek"}

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
