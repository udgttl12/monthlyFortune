import unittest
from dataclasses import dataclass
from datetime import date

from app.schemas.ai_retention import (
    ActionCalendarDay,
    ActionCalendarRequest,
    ActionCalendarResponse,
    DailyBriefRequest,
)
from app.services.ai_retention_service import AIRetentionService
from app.services.cache import TTLCache
from app.services.chart_engine import NatalProfile
from app.services.timing_signal_service import TimingSignalService
from app.services.transit_engine import DailyTransitScore, MonthlyTransitAnalysis, TransitEvent, TransitWindow


class AiRetentionSchemaTestCase(unittest.TestCase):
    def test_calendar_response_uses_camel_case_aliases(self) -> None:
        response = ActionCalendarResponse(
            year=2026,
            month=5,
            profileSummary="profile",
            llmEnhanced=False,
            days=[
                ActionCalendarDay(
                    date=date(2026, 5, 10),
                    score=7,
                    tone="supportive",
                    title="좋은 흐름",
                    action="중요한 연락을 오전에 보낸다.",
                    avoid="충동적인 지출은 미룬다.",
                    reason="관계와 일 점수가 동시에 높다.",
                    categories=["career", "love"],
                )
            ],
        )

        payload = response.model_dump(mode="json", by_alias=True)

        self.assertIn("profileSummary", payload)
        self.assertIn("llmEnhanced", payload)
        self.assertEqual(payload["days"][0]["date"], "2026-05-10")

    def test_request_models_accept_existing_birth_shape(self) -> None:
        request = ActionCalendarRequest(
            birthDate="1990-01-01",
            birthTime="09:00",
            city="Seoul",
            countryCode="KR",
            year=2026,
            month=5,
        )

        self.assertEqual(request.country_code, "KR")
        self.assertEqual(request.birth_time, "09:00")


class TimingSignalServiceTestCase(unittest.TestCase):
    def test_builds_serializable_daily_signal(self) -> None:
        service = TimingSignalService()
        day = build_day(date(2026, 5, 10), 2.4)

        signal = service.build_daily_signal(day)

        self.assertEqual(signal.date, date(2026, 5, 10))
        self.assertEqual(signal.total_score, 2.4)
        self.assertIn("커리어", signal.positive_signals[0])

    def test_fallback_calendar_day_maps_score_and_tone(self) -> None:
        service = TimingSignalService()
        day = build_day(date(2026, 5, 11), -1.8)

        item = service.build_fallback_calendar_day(day)

        self.assertEqual(item.score, 3)
        self.assertEqual(item.tone, "challenging")
        self.assertIn("주의", item.reason)


class DisabledLLMClient:
    enabled = False
    model = "fallback"
    prompt_version = "retention-test-v1"
    provider = "none"

    def generate_action_calendar(self, *args, **kwargs):
        return None

    def generate_daily_brief(self, *args, **kwargs):
        return None

    def answer_timing_question(self, *args, **kwargs):
        return None


class FakeAstrologyService:
    def build_birth_context(self, request):
        return FakeContext(request=request, natal_chart=object())


class FakeChartEngine:
    def build_natal_profile(self, natal_chart):
        return NatalProfile(
            sun_sign="Sagittarius",
            moon_sign="Scorpio",
            rising_sign="Cancer",
            dominant_element="water",
            dominant_element_label="물",
            focus_areas=("관계", "커리어"),
            base_scores={"career": 4.0, "money": 3.0, "love": 5.0, "risk": 2.0},
        )


class FakeTransitEngine:
    def calculate_monthly_transit(self, *args, **kwargs):
        days = [build_day(date(2026, 5, day), 2.0 if day == 10 else -1.0) for day in range(1, 32)]
        return MonthlyTransitAnalysis(
            year=2026,
            month=5,
            title="테스트 월간 흐름",
            focus_area_keys=("career", "love"),
            focus_area_labels=("커리어", "관계"),
            top_theme_key="career",
            top_theme_label="커리어",
            intensity_score=6,
            total_score=3.2,
            category_totals={"career": 1.0, "money": 0.2, "love": 1.4, "risk": -0.3},
            daily_scores=days,
            lucky_days=[days[9]],
            caution_days=[days[0]],
            evidence=days[9].positive_events,
            lucky_window=TransitWindow(start_date=date(2026, 5, 10), end_date=date(2026, 5, 12), label="5/10-5/12"),
            caution_window=TransitWindow(start_date=date(2026, 5, 1), end_date=date(2026, 5, 3), label="5/1-5/3"),
        )


@dataclass
class FakeContext:
    request: object
    natal_chart: object


class AIRetentionServiceTestCase(unittest.TestCase):
    def build_service(self) -> AIRetentionService:
        return AIRetentionService(
            astrology_service=FakeAstrologyService(),
            chart_engine=FakeChartEngine(),
            transit_engine=FakeTransitEngine(),
            timing_signal_service=TimingSignalService(),
            calendar_cache=TTLCache(ttl_seconds=60),
            daily_cache=TTLCache(ttl_seconds=60),
            coach_cache=TTLCache(ttl_seconds=60),
            llm_client=DisabledLLMClient(),
        )

    def test_daily_brief_returns_deterministic_fallback_without_llm(self) -> None:
        service = self.build_service()
        request = DailyBriefRequest(
            birthDate="1990-01-01",
            birthTime="09:00",
            city="Seoul",
            countryCode="KR",
            year=2026,
            month=5,
            targetDate=date(2026, 5, 10),
        )

        response = service.daily_brief(request)

        self.assertEqual(response.date, date(2026, 5, 10))
        self.assertFalse(response.llm_enhanced)
        self.assertGreaterEqual(response.score, 1)
        self.assertLessEqual(response.score, 10)

    def test_calendar_result_is_cached(self) -> None:
        service = self.build_service()
        request = ActionCalendarRequest(
            birthDate="1990-01-01",
            birthTime="09:00",
            city="Seoul",
            countryCode="KR",
            year=2026,
            month=5,
        )

        first = service.action_calendar(request)
        second = service.action_calendar(request)

        self.assertEqual(first.days[0].title, second.days[0].title)
        self.assertFalse(first.llm_enhanced)


def build_day(target_date: date, total_score: float) -> DailyTransitScore:
    positive = total_score >= 0
    event = TransitEvent(
        date=target_date,
        theme="career",
        tone="supportive" if positive else "challenging",
        score=total_score,
        headline="커리어 흐름이 살아납니다." if positive else "주의가 필요한 흐름입니다.",
        detail="테스트 근거입니다.",
    )
    return DailyTransitScore(
        date=target_date,
        total_score=total_score,
        category_scores={"career": total_score, "money": 0.0, "love": 0.0, "risk": 0.0},
        positive_events=[event] if positive else [],
        negative_events=[] if positive else [event],
    )
