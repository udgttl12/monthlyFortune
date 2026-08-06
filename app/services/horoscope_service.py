from typing import Optional

from app.schemas.chart import NatalChartRequest
from app.schemas.horoscope import (
    MonthlyHoroscopeRequest,
    MonthlyHoroscopeResponse,
    YearlyHoroscopeRequest,
    YearlyHoroscopeResponse,
)
from app.services.astrology_service import AstrologyService
from app.services.cache import TTLCache
from app.services.chart_engine import ChartEngine
from app.services.interpretation_engine import InterpretationEngine
from app.services.persistent_cache import PersistentCache
from app.services.transit_engine import MonthlyTransitAnalysis, TransitEngine
from app.services.xai_service import MonthlyReportClient


class HoroscopeService:
    def __init__(
        self,
        astrology_service: AstrologyService,
        chart_engine: ChartEngine,
        transit_engine: TransitEngine,
        interpretation_engine: InterpretationEngine,
        yearly_cache: TTLCache,
        monthly_cache: TTLCache,
        analysis_cache: TTLCache,
        xai_service: Optional[MonthlyReportClient] = None,
        persistent_cache: Optional[PersistentCache] = None,
    ) -> None:
        self.astrology_service = astrology_service
        self.chart_engine = chart_engine
        self.transit_engine = transit_engine
        self.interpretation_engine = interpretation_engine
        self.yearly_cache = yearly_cache
        self.monthly_cache = monthly_cache
        self.analysis_cache = analysis_cache
        self.xai_service = xai_service or MonthlyReportClient.from_env()
        self.persistent_cache = persistent_cache
        self.analysis_version = "horoscope-analysis-v1"

    def yearly_horoscope(self, request: YearlyHoroscopeRequest) -> YearlyHoroscopeResponse:
        cache_key = self._yearly_cache_key(request)
        cached = self.yearly_cache.get(cache_key)
        if cached is not None:
            return YearlyHoroscopeResponse(**cached)
        persistent = self._persistent_get("horoscope_yearly", cache_key)
        if persistent is not None:
            self.yearly_cache.set(cache_key, persistent)
            return YearlyHoroscopeResponse(**persistent)

        context = self.astrology_service.build_birth_context(self._to_chart_request(request))
        profile = self.chart_engine.build_natal_profile(context.natal_chart)
        analyses = [
            self._get_monthly_analysis(context=context, profile=profile, year=request.year, month=month)
            for month in range(1, 13)
        ]
        response = self.interpretation_engine.build_yearly_response(
            year=request.year,
            profile=profile,
            monthly_analyses=analyses,
        )
        payload = response.model_dump(mode="json", by_alias=True)
        self.yearly_cache.set(cache_key, payload)
        self._persistent_set("horoscope_yearly", cache_key, payload)
        return response

    def monthly_horoscope(self, request: MonthlyHoroscopeRequest) -> MonthlyHoroscopeResponse:
        cache_key = self._monthly_cache_key(request)
        cached = self.monthly_cache.get(cache_key)
        if cached is not None:
            return MonthlyHoroscopeResponse(**cached)
        persistent = self._persistent_get("horoscope_monthly", cache_key)
        if persistent is not None:
            self.monthly_cache.set(cache_key, persistent)
            return MonthlyHoroscopeResponse(**persistent)

        context = self.astrology_service.build_birth_context(self._to_chart_request(request))
        profile = self.chart_engine.build_natal_profile(context.natal_chart)
        analysis = self._get_monthly_analysis(
            context=context,
            profile=profile,
            year=request.year,
            month=request.month,
        )
        fallback = self.interpretation_engine.build_monthly_response(analysis=analysis, profile=profile)
        enhancement = self.xai_service.enhance_monthly_report(
            profile=profile,
            analysis=analysis,
            fallback_payload={
                "summary": fallback.summary,
                "sections": fallback.sections.model_dump(by_alias=True),
                "luckyDates": [item.model_dump(mode="json", by_alias=True) for item in fallback.lucky_dates],
                "cautionDates": [item.model_dump(mode="json", by_alias=True) for item in fallback.caution_dates],
                "evidence": [item.model_dump(mode="json", by_alias=True) for item in fallback.evidence],
            },
        )
        response = self.interpretation_engine.apply_llm_enhancement(fallback, enhancement)
        payload = response.model_dump(mode="json", by_alias=True)
        self.monthly_cache.set(cache_key, payload)
        self._persistent_set("horoscope_monthly", cache_key, payload)
        return response

    def _persistent_get(self, namespace: str, cache_key: str):
        if self.persistent_cache is None:
            return None
        return self.persistent_cache.get(namespace, cache_key)

    def _persistent_set(self, namespace: str, cache_key: str, payload: dict) -> None:
        if self.persistent_cache is None:
            return
        self.persistent_cache.set(namespace, cache_key, payload)

    def _get_monthly_analysis(
        self,
        context,
        profile,
        year: int,
        month: int,
    ) -> MonthlyTransitAnalysis:
        cache_key = self._analysis_cache_key(context.request, year, month)
        cached = self.analysis_cache.get(cache_key)
        if cached is not None:
            return cached

        analysis = self.transit_engine.calculate_monthly_transit(
            context=context,
            profile=profile,
            year=year,
            month=month,
        )
        self.analysis_cache.set(cache_key, analysis)
        return analysis

    def _to_chart_request(self, request: YearlyHoroscopeRequest) -> NatalChartRequest:
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

    def _yearly_cache_key(self, request: YearlyHoroscopeRequest) -> str:
        return f"yearly:{self.analysis_version}:{self._birth_signature(request)}:{request.year}"

    def _analysis_cache_key(self, request: NatalChartRequest, year: int, month: int) -> str:
        return f"analysis:{self.analysis_version}:{self._birth_signature(request)}:{year}:{month}"

    def _monthly_cache_key(self, request: MonthlyHoroscopeRequest) -> str:
        if self.xai_service.enabled:
            llm_key = f"{self.xai_service.provider}:{self.xai_service.model}"
        else:
            llm_key = "none:fallback"
        return (
            f"monthly:{self.analysis_version}:{self.xai_service.prompt_version}:{llm_key}:"
            f"{self._birth_signature(request)}:{request.year}:{request.month}"
        )
