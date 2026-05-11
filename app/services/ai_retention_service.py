import hashlib
from typing import Optional

from app.schemas.ai_retention import (
    ActionCalendarRequest,
    ActionCalendarResponse,
    CoachRecommendedDate,
    CoachRequest,
    CoachResponse,
    DailyBriefRequest,
    DailyBriefResponse,
)
from app.schemas.chart import NatalChartRequest
from app.services.astrology_service import AstrologyService
from app.services.cache import TTLCache
from app.services.chart_engine import ChartEngine, NatalProfile
from app.services.llm_retention_client import LLMRetentionClient
from app.services.timing_signal_service import TimingSignalService
from app.services.transit_engine import MonthlyTransitAnalysis, TransitEngine


class AIRetentionService:
    def __init__(
        self,
        astrology_service: AstrologyService,
        chart_engine: ChartEngine,
        transit_engine: TransitEngine,
        timing_signal_service: TimingSignalService,
        calendar_cache: TTLCache,
        daily_cache: TTLCache,
        coach_cache: TTLCache,
        llm_client: Optional[LLMRetentionClient] = None,
    ) -> None:
        self.astrology_service = astrology_service
        self.chart_engine = chart_engine
        self.transit_engine = transit_engine
        self.timing_signal_service = timing_signal_service
        self.calendar_cache = calendar_cache
        self.daily_cache = daily_cache
        self.coach_cache = coach_cache
        self.llm_client = llm_client or LLMRetentionClient.from_env()
        self.analysis_version = "ai-retention-v1"

    def action_calendar(self, request: ActionCalendarRequest) -> ActionCalendarResponse:
        cache_key = self._calendar_cache_key(request)
        cached = self.calendar_cache.get(cache_key)
        if cached is not None:
            return ActionCalendarResponse(**cached)

        profile, analysis = self._profile_and_analysis(request)
        signals = self.timing_signal_service.build_month_signals(analysis)
        fallback_days = [
            self.timing_signal_service.build_fallback_calendar_day(day)
            for day in analysis.daily_scores
        ]
        enhancement = self.llm_client.generate_action_calendar(
            profile=profile,
            analysis=analysis,
            signals=signals,
            fallback_days=fallback_days,
        )
        response = ActionCalendarResponse(
            year=request.year,
            month=request.month,
            profileSummary=self._profile_summary(profile),
            llmEnhanced=enhancement is not None,
            days=enhancement.days if enhancement is not None else fallback_days,
        )
        self.calendar_cache.set(cache_key, response.model_dump(mode="json", by_alias=True))
        return response

    def daily_brief(self, request: DailyBriefRequest) -> DailyBriefResponse:
        cache_key = self._daily_cache_key(request)
        cached = self.daily_cache.get(cache_key)
        if cached is not None:
            return DailyBriefResponse(**cached)

        profile, analysis = self._profile_and_analysis(request)
        day = self.timing_signal_service.find_day(analysis, request.target_date)
        fallback = self.timing_signal_service.build_fallback_daily_brief(day)
        enhancement = self.llm_client.generate_daily_brief(
            profile=profile,
            analysis=analysis,
            signal=self.timing_signal_service.build_daily_signal(day),
        )
        response = fallback if enhancement is None else DailyBriefResponse(
            date=day.date,
            score=fallback.score,
            tone=fallback.tone,
            headline=enhancement.headline,
            summary=enhancement.summary,
            bestTimeHint=enhancement.best_time_hint,
            avoidTimeHint=enhancement.avoid_time_hint,
            action=enhancement.action,
            avoid=enhancement.avoid,
            reflectionPrompt=enhancement.reflection_prompt,
            llmEnhanced=True,
        )
        self.daily_cache.set(cache_key, response.model_dump(mode="json", by_alias=True))
        return response

    def timing_coach(self, request: CoachRequest) -> CoachResponse:
        cache_key = self._coach_cache_key(request)
        cached = self.coach_cache.get(cache_key)
        if cached is not None:
            return CoachResponse(**cached)

        profile, analysis = self._profile_and_analysis(request)
        signals = self.timing_signal_service.build_month_signals(analysis)
        enhancement = self.llm_client.answer_timing_question(
            profile=profile,
            analysis=analysis,
            signals=signals,
            question=request.question,
        )
        if enhancement is None:
            best = analysis.lucky_days[0] if analysis.lucky_days else analysis.daily_scores[0]
            caution = analysis.caution_days[0] if analysis.caution_days else analysis.daily_scores[-1]
            response = CoachResponse(
                question=request.question,
                answer="이번 달 흐름에서는 좋은 날과 주의할 날을 나누어 작게 실행하는 방식이 안정적입니다.",
                recommendedDates=[
                    CoachRecommendedDate(date=best.date, label="실행 후보", reason="월간 점수가 높은 날입니다.")
                ],
                cautionDates=[
                    CoachRecommendedDate(date=caution.date, label="속도 조절", reason="월간 점수가 낮은 날입니다.")
                ],
                firstAction="오늘 질문의 핵심 조건을 한 문장으로 정리합니다.",
                messageDraft="상황을 확인해보고 신중하게 답드리겠습니다.",
                reasoningSummary="월간 일별 점수의 상위일과 하위일을 기준으로 정리했습니다.",
                disclaimer="운세는 의사결정 보조 자료입니다. 중요한 결정은 현실 정보와 함께 판단하세요.",
                llmEnhanced=False,
            )
        else:
            response = CoachResponse(
                question=request.question,
                answer=enhancement.answer,
                recommendedDates=enhancement.recommended_dates,
                cautionDates=enhancement.caution_dates,
                firstAction=enhancement.first_action,
                messageDraft=enhancement.message_draft,
                reasoningSummary=enhancement.reasoning_summary,
                disclaimer=enhancement.disclaimer,
                llmEnhanced=True,
            )
        self.coach_cache.set(cache_key, response.model_dump(mode="json", by_alias=True))
        return response

    def _profile_and_analysis(self, request: ActionCalendarRequest) -> tuple[NatalProfile, MonthlyTransitAnalysis]:
        context = self.astrology_service.build_birth_context(self._to_chart_request(request))
        profile = self.chart_engine.build_natal_profile(context.natal_chart)
        analysis = self.transit_engine.calculate_monthly_transit(
            context=context,
            profile=profile,
            year=request.year,
            month=request.month,
        )
        return profile, analysis

    def _to_chart_request(self, request: ActionCalendarRequest) -> NatalChartRequest:
        return NatalChartRequest(
            birthDate=request.birth_date.isoformat(),
            birthTime=request.birth_time,
            city=request.city,
            countryCode=request.country_code,
            timezone=request.timezone,
        )

    def _birth_signature(self, request: NatalChartRequest) -> str:
        return ":".join(
            [
                request.birth_date.isoformat(),
                request.birth_time,
                request.city.casefold(),
                request.country_code,
                request.timezone or "",
            ]
        )

    def _calendar_cache_key(self, request: ActionCalendarRequest) -> str:
        return f"calendar:{self.analysis_version}:{self._birth_signature(request)}:{request.year}:{request.month}:{self._llm_key()}"

    def _daily_cache_key(self, request: DailyBriefRequest) -> str:
        return f"daily:{self.analysis_version}:{self._birth_signature(request)}:{request.target_date.isoformat()}:{self._llm_key()}"

    def _coach_cache_key(self, request: CoachRequest) -> str:
        question_hash = hashlib.sha256(request.question.strip().casefold().encode("utf-8")).hexdigest()[:16]
        return f"coach:{self.analysis_version}:{self._birth_signature(request)}:{request.year}:{request.month}:{question_hash}:{self._llm_key()}"

    def _llm_key(self) -> str:
        if not self.llm_client.enabled:
            return f"{self.llm_client.prompt_version}:none:fallback"
        return f"{self.llm_client.prompt_version}:{self.llm_client.provider}:{self.llm_client.model}"

    def _profile_summary(self, profile: NatalProfile) -> str:
        return (
            f"태양 {profile.sun_sign}, 달 {profile.moon_sign}, 상승 {profile.rising_sign} 흐름을 바탕으로 "
            f"{profile.focus_areas[0]}와 {profile.focus_areas[1]} 리듬을 우선 확인합니다."
        )
