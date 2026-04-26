import json
import unittest
from datetime import date
from unittest.mock import Mock, patch

import httpx

from app.schemas.horoscope import HoroscopeSections
from app.services.chart_engine import NatalProfile
from app.services.transit_engine import MonthlyTransitAnalysis, TransitWindow
from app.services.xai_service import XAIService


class XAIServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.service = XAIService(api_key="test-key", model="test-model", timeout_seconds=5)
        self.profile = NatalProfile(
            sun_sign="Sagittarius",
            moon_sign="Scorpio",
            rising_sign="Cancer",
            dominant_element="water",
            dominant_element_label="물",
            focus_areas=("관계", "커리어"),
            base_scores={"career": 4.0, "money": 3.0, "love": 5.0, "risk": 2.0},
        )
        self.analysis = MonthlyTransitAnalysis(
            year=2026,
            month=4,
            title="관계 정비가 잘 먹히는 달",
            focus_area_keys=("love", "career"),
            focus_area_labels=("관계", "커리어"),
            top_theme_key="love",
            top_theme_label="관계",
            intensity_score=7,
            total_score=3.2,
            category_totals={"career": 1.0, "money": 0.2, "love": 2.3, "risk": -0.3},
            daily_scores=[],
            lucky_days=[],
            caution_days=[],
            evidence=[],
            lucky_window=TransitWindow(
                start_date=date(2026, 4, 10),
                end_date=date(2026, 4, 12),
                label="4/10-4/12 관계 흐름이 열리는 구간",
            ),
            caution_window=TransitWindow(
                start_date=date(2026, 4, 21),
                end_date=date(2026, 4, 23),
                label="4/21-4/23 관계 속도 조절이 필요한 구간",
            ),
        )
        self.fallback_payload = {
            "summary": "기본 요약",
            "sections": HoroscopeSections(
                career="기본 커리어",
                money="기본 재정",
                love="기본 관계",
                risk="기본 리스크",
            ).model_dump(by_alias=True),
            "luckyDates": [
                {"date": "2026-04-10", "label": "기본 좋은 날", "reason": "기본 이유"},
                {"date": "2026-04-12", "label": "기본 좋은 날", "reason": "기본 이유"},
                {"date": "2026-04-16", "label": "기본 좋은 날", "reason": "기본 이유"},
            ],
            "cautionDates": [
                {"date": "2026-04-05", "label": "기본 주의 날", "reason": "기본 이유"},
                {"date": "2026-04-21", "label": "기본 주의 날", "reason": "기본 이유"},
                {"date": "2026-04-27", "label": "기본 주의 날", "reason": "기본 이유"},
            ],
            "evidence": [
                {"date": "2026-04-10", "headline": "기본 근거", "detail": "기본 설명", "tone": "supportive"}
            ],
        }

    def test_successfully_parses_structured_output(self) -> None:
        payload = {
            "summary": "AI 요약",
            "sections": {
                "career": "AI 커리어",
                "money": "AI 재정",
                "love": "AI 관계",
                "risk": "AI 리스크",
            },
            "luckyDates": [
                {"label": "좋은 날 1", "reason": "이유 1"},
                {"label": "좋은 날 2", "reason": "이유 2"},
                {"label": "좋은 날 3", "reason": "이유 3"},
            ],
            "cautionDates": [
                {"label": "주의 날 1", "reason": "주의 1"},
                {"label": "주의 날 2", "reason": "주의 2"},
                {"label": "주의 날 3", "reason": "주의 3"},
            ],
            "evidence": [{"headline": "근거", "detail": "설명"}],
        }
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "output": [
                {
                    "content": [
                        {
                            "text": json.dumps(payload, ensure_ascii=False)
                        }
                    ]
                }
            ]
        }

        with patch("app.services.xai_service.httpx.post", return_value=response):
            result = self.service.enhance_monthly_report(
                profile=self.profile,
                analysis=self.analysis,
                fallback_payload=self.fallback_payload,
            )

        self.assertIsNotNone(result)
        self.assertEqual(result.summary, "AI 요약")
        self.assertEqual(result.sections.love, "AI 관계")

    def test_returns_none_on_http_timeout(self) -> None:
        with patch("app.services.xai_service.httpx.post", side_effect=httpx.TimeoutException("timeout")):
            result = self.service.enhance_monthly_report(
                profile=self.profile,
                analysis=self.analysis,
                fallback_payload=self.fallback_payload,
            )

        self.assertIsNone(result)

    def test_returns_none_on_malformed_json(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "output": [{"content": [{"text": "{not-json"}]}]
        }

        with patch("app.services.xai_service.httpx.post", return_value=response):
            result = self.service.enhance_monthly_report(
                profile=self.profile,
                analysis=self.analysis,
                fallback_payload=self.fallback_payload,
            )

        self.assertIsNone(result)
