from app.schemas.horoscope import MonthlyHoroscopeResponse
from app.services.cache import TTLCache
from app.services.chart_engine import ChartEngine
from app.services.interpretation_engine import InterpretationEngine
from app.services.transit_engine import TransitEngine


class HoroscopeService:
    def __init__(
        self,
        chart_engine: ChartEngine,
        transit_engine: TransitEngine,
        interpretation_engine: InterpretationEngine,
        cache: TTLCache,
    ) -> None:
        self.chart_engine = chart_engine
        self.transit_engine = transit_engine
        self.interpretation_engine = interpretation_engine
        self.cache = cache

    def monthly_horoscope(self, year: int, month: int) -> MonthlyHoroscopeResponse:
        cache_key = f"monthly:{year}:{month}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return MonthlyHoroscopeResponse(**cached)

        chart = self.chart_engine.build_monthly_chart(year=year, month=month)
        transit = self.transit_engine.calculate_monthly_transit(chart)
        interpretation = self.interpretation_engine.interpret(chart, transit)

        self.cache.set(cache_key, interpretation)
        return MonthlyHoroscopeResponse(**interpretation)
