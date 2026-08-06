import unittest
from typing import Optional

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
    def __init__(
        self,
        response: Optional[MonthlyHoroscopeLLMResponse],
        provider: str = "test-provider",
    ) -> None:
        self.response = response
        self.calls = 0
        self.enabled = True
        self.provider = provider
        self.model = "test-model"
        self.prompt_version = "test-prompt"

    def enhance_monthly_report(self, *args, **kwargs) -> Optional[MonthlyHoroscopeLLMResponse]:
        self.calls += 1
        return self.response


class RecordingPersistentCache:
    def __init__(self) -> None:
        self.store = {}
        self.gets = 0
        self.sets = 0

    def get(self, namespace: str, cache_key: str):
        self.gets += 1
        return self.store.get((namespace, cache_key))

    def set(self, namespace: str, cache_key: str, payload: dict) -> None:
        self.sets += 1
        self.store[(namespace, cache_key)] = payload


class HoroscopeServiceTestCase(unittest.TestCase):
    def build_service(self, xai_service, persistent_cache=None) -> HoroscopeService:
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
            persistent_cache=persistent_cache,
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

    def test_monthly_reuses_persistent_cache_without_llm_call(self) -> None:
        persistent_cache = RecordingPersistentCache()
        first_xai_service = RecordingXAIService(None)
        first_service = self.build_service(first_xai_service, persistent_cache=persistent_cache)
        request = self.build_request()

        first = first_service.monthly_horoscope(request)

        second_xai_service = RecordingXAIService(None)
        second_service = self.build_service(second_xai_service, persistent_cache=persistent_cache)
        second = second_service.monthly_horoscope(request)

        self.assertFalse(second.llm_enhanced)
        self.assertEqual(second.summary, first.summary)
        self.assertEqual(first_xai_service.calls, 1)
        self.assertEqual(second_xai_service.calls, 0)
        self.assertGreaterEqual(persistent_cache.sets, 1)

    def test_monthly_cache_key_separates_providers(self) -> None:
        persistent_cache = RecordingPersistentCache()
        request = self.build_request()

        first_xai_service = RecordingXAIService(None, provider="xai")
        self.build_service(first_xai_service, persistent_cache=persistent_cache).monthly_horoscope(request)

        second_xai_service = RecordingXAIService(None, provider="upstage")
        self.build_service(second_xai_service, persistent_cache=persistent_cache).monthly_horoscope(request)

        # provider가 다르면 캐시 키가 갈려야 한다. 같은 키를 쓰면 두 번째 호출이 0이 된다.
        self.assertEqual(first_xai_service.calls, 1)
        self.assertEqual(second_xai_service.calls, 1)
        self.assertEqual(len(persistent_cache.store), 2)
