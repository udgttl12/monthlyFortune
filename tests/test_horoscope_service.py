import unittest

from app.schemas.horoscope import MonthlyHoroscopeLLMResponse, MonthlyHoroscopeRequest
from app.services.astrology_service import AstrologyService
from app.services.cache import TTLCache
from app.services.chart_engine import ChartEngine
from app.services.geocoding_service import GeocodingService
from app.services.horoscope_service import HoroscopeService
from app.services.interpretation_engine import InterpretationEngine
from app.services.natal_chart_engine import NatalChartEngine
from app.services.transit_engine import TransitEngine


class RecordingXAIService:
    def __init__(self, response: MonthlyHoroscopeLLMResponse | None) -> None:
        self.response = response
        self.calls = 0
        self.enabled = True
        self.model = "test-model"
        self.prompt_version = "test-prompt"

    def enhance_monthly_report(self, *args, **kwargs) -> MonthlyHoroscopeLLMResponse | None:
        self.calls += 1
        return self.response


class HoroscopeServiceTestCase(unittest.TestCase):
    def build_service(self, xai_service) -> HoroscopeService:
        natal_chart_engine = NatalChartEngine()
        return HoroscopeService(
            astrology_service=AstrologyService(
                natal_chart_engine=natal_chart_engine,
                geocoding_service=GeocodingService(cache=TTLCache(ttl_seconds=3600)),
                cache=TTLCache(ttl_seconds=3600),
            ),
            chart_engine=ChartEngine(),
            transit_engine=TransitEngine(natal_chart_engine=natal_chart_engine),
            interpretation_engine=InterpretationEngine(),
            yearly_cache=TTLCache(ttl_seconds=3600),
            monthly_cache=TTLCache(ttl_seconds=3600),
            analysis_cache=TTLCache(ttl_seconds=3600),
            xai_service=xai_service,
        )

    def build_request(self) -> MonthlyHoroscopeRequest:
        return MonthlyHoroscopeRequest(
            birthDate="1988-12-06",
            birthTime="19:59",
            city="Busan",
            countryCode="KR",
            timezone="Asia/Seoul",
            year=2026,
            month=4,
        )

    def test_monthly_uses_llm_response_when_available(self) -> None:
        xai_service = RecordingXAIService(
            MonthlyHoroscopeLLMResponse(
                summary="AI 요약입니다.",
                sections={
                    "career": "AI 커리어",
                    "money": "AI 재정",
                    "love": "AI 관계",
                    "risk": "AI 리스크",
                },
                luckyDates=[
                    {"label": "기회가 열리는 날", "reason": "AI 이유 1"},
                    {"label": "성과가 붙는 날", "reason": "AI 이유 2"},
                    {"label": "리듬이 맞는 날", "reason": "AI 이유 3"},
                ],
                cautionDates=[
                    {"label": "속도 조절", "reason": "AI 주의 1"},
                    {"label": "일정 여유 확보", "reason": "AI 주의 2"},
                    {"label": "감정 과열 주의", "reason": "AI 주의 3"},
                ],
                evidence=[
                    {"headline": "AI 근거 1", "detail": "AI 설명 1"},
                    {"headline": "AI 근거 2", "detail": "AI 설명 2"},
                    {"headline": "AI 근거 3", "detail": "AI 설명 3"},
                    {"headline": "AI 근거 4", "detail": "AI 설명 4"},
                ],
            )
        )
        service = self.build_service(xai_service)

        response = service.monthly_horoscope(self.build_request())

        self.assertTrue(response.llm_enhanced)
        self.assertEqual(response.summary, "AI 요약입니다.")
        self.assertEqual(response.sections.career, "AI 커리어")
        self.assertEqual(response.lucky_dates[0].label, "기회가 열리는 날")
        self.assertEqual(response.evidence[0].headline, "AI 근거 1")

    def test_monthly_falls_back_and_hits_cache_when_llm_unavailable(self) -> None:
        xai_service = RecordingXAIService(None)
        service = self.build_service(xai_service)
        request = self.build_request()

        first = service.monthly_horoscope(request)
        second = service.monthly_horoscope(request)

        self.assertFalse(first.llm_enhanced)
        self.assertEqual(first.summary, second.summary)
        self.assertEqual(xai_service.calls, 1)
