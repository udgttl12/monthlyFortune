from datetime import datetime

from app.core.chart_engine import ChartEngine
from app.core.interpretation_engine import InterpretationEngine
from app.core.transit_engine import TransitEngine
from app.schemas.chart import ChartRequest, ChartResponse
from app.schemas.horoscope import HoroscopeCards, MonthlyHoroscopeResponse, TransitEvent


class AstrologyService:
    def __init__(self) -> None:
        self.chart_engine = ChartEngine()
        self.transit_engine = TransitEngine()
        self.interpretation_engine = InterpretationEngine()

    def build_chart(self, request: ChartRequest) -> ChartResponse:
        birth_dt = self._make_birth_datetime(request)
        chart_data = self.chart_engine.calculate_chart(
            birth_dt=birth_dt,
            latitude=request.latitude,
            longitude=request.longitude,
        )
        return ChartResponse(name=request.name, **chart_data)

    def build_monthly_horoscope(self, request: ChartRequest, year: int, month: int) -> MonthlyHoroscopeResponse:
        chart = self.build_chart(request)
        events = self.transit_engine.calculate_monthly_transits(year, month, chart.planets)
        cards = self.interpretation_engine.build_rule_based_summary(chart.aspects, events)
        cards = self.interpretation_engine.enhance_with_llm(cards)

        return MonthlyHoroscopeResponse(
            name=request.name,
            year=year,
            month=month,
            cards=HoroscopeCards(**cards),
            events=[TransitEvent(**event) for event in events],
        )

    @staticmethod
    def _make_birth_datetime(request: ChartRequest) -> datetime:
        hour, minute = map(int, request.birth_time.split(":"))
        return datetime(
            request.birth_date.year,
            request.birth_date.month,
            request.birth_date.day,
            hour,
            minute,
        )
