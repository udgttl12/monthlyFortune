import json
import os
import unittest
from datetime import date
from unittest.mock import Mock, patch

import httpx

from app.schemas.horoscope import HoroscopeSections
from app.services.chart_engine import NatalProfile
from app.services.transit_engine import MonthlyTransitAnalysis, TransitWindow
from app.services.xai_service import MonthlyReportClient, XAIService


class MonthlyFixtureMixin:
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

    def llm_payload(self) -> dict:
        return {
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

    def enhance(self, service) -> object:
        return service.enhance_monthly_report(
            profile=self.profile,
            analysis=self.analysis,
            fallback_payload=self.fallback_payload,
        )


class XAIServiceTestCase(MonthlyFixtureMixin, unittest.TestCase):
    def test_successfully_parses_structured_output(self) -> None:
        payload = self.llm_payload()
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

    def test_xai_still_posts_to_responses_endpoint(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "output": [{"content": [{"text": json.dumps(self.llm_payload(), ensure_ascii=False)}]}]
        }

        with patch("app.services.xai_service.httpx.post", return_value=response) as post:
            self.enhance(self.service)

        self.assertEqual(post.call_args.args[0], "https://api.x.ai/v1/responses")
        self.assertIn("text", post.call_args.kwargs["json"])


class MonthlyReportClientUpstageTestCase(MonthlyFixtureMixin, unittest.TestCase):
    def upstage_client(self, **overrides) -> MonthlyReportClient:
        kwargs = {
            "provider": "upstage",
            "api_key": "test-key",
            "model": "solar-pro3",
            "timeout_seconds": 5,
        }
        kwargs.update(overrides)
        return MonthlyReportClient(**kwargs)

    def chat_completion_response(self, content: str) -> Mock:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"choices": [{"message": {"content": content}}]}
        return response

    def test_upstage_provider_posts_to_chat_completions(self) -> None:
        response = self.chat_completion_response(json.dumps(self.llm_payload(), ensure_ascii=False))

        with patch("app.services.xai_service.httpx.post", return_value=response) as post:
            result = self.enhance(self.upstage_client())

        self.assertIsNotNone(result)
        self.assertEqual(result.summary, "AI 요약")
        self.assertEqual(post.call_args.args[0], "https://api.upstage.ai/v1/chat/completions")

    def test_upstage_request_uses_flattened_schema(self) -> None:
        response = self.chat_completion_response(json.dumps(self.llm_payload(), ensure_ascii=False))

        with patch("app.services.xai_service.httpx.post", return_value=response) as post:
            self.enhance(self.upstage_client())

        response_format = post.call_args.kwargs["json"]["response_format"]
        self.assertEqual(response_format["type"], "json_schema")
        self.assertEqual(response_format["json_schema"]["name"], "monthly_horoscope_enhancement")
        self.assertIs(response_format["json_schema"]["strict"], True)
        self.assertNotIn("$ref", json.dumps(response_format["json_schema"]["schema"]))
        self.assertIs(response_format["json_schema"]["schema"]["additionalProperties"], False)

    def test_upstage_reads_content_parts_array(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "reasoning": "결정론적 초안을 다듬는다.",
                        "content": [{"text": json.dumps(self.llm_payload(), ensure_ascii=False)}],
                    }
                }
            ]
        }

        with patch("app.services.xai_service.httpx.post", return_value=response):
            result = self.enhance(self.upstage_client())

        self.assertIsNotNone(result)
        self.assertEqual(result.sections.love, "AI 관계")

    def test_upstage_returns_none_on_http_error(self) -> None:
        with patch(
            "app.services.xai_service.httpx.post", side_effect=httpx.TimeoutException("timeout")
        ):
            result = self.enhance(self.upstage_client())

        self.assertIsNone(result)

    def test_upstage_returns_none_on_malformed_json(self) -> None:
        response = self.chat_completion_response("{not-json")

        with patch("app.services.xai_service.httpx.post", return_value=response):
            result = self.enhance(self.upstage_client())

        self.assertIsNone(result)


class MonthlyReportClientFromEnvTestCase(unittest.TestCase):
    def test_defaults_to_xai_with_legacy_env(self) -> None:
        # MONTHLY_LLM_* 없이 기존 XAI_* 만 있어도 오늘과 동일하게 동작해야 한다.
        with patch.dict(
            os.environ,
            {
                "XAI_API_KEY": "legacy-key",
                "XAI_MODEL": "grok-legacy",
                "XAI_TIMEOUT_SECONDS": "30",
            },
            clear=True,
        ):
            client = MonthlyReportClient.from_env()

        self.assertEqual(client.provider, "xai")
        self.assertEqual(client.api_key, "legacy-key")
        self.assertEqual(client.model, "grok-legacy")
        self.assertEqual(client.timeout_seconds, 30.0)
        self.assertTrue(client.enabled)

    def test_selects_upstage(self) -> None:
        with patch.dict(
            os.environ,
            {"MONTHLY_LLM_PROVIDER": "upstage", "UPSTAGE_API_KEY": "up-key"},
            clear=True,
        ):
            client = MonthlyReportClient.from_env()

        self.assertEqual(client.provider, "upstage")
        self.assertEqual(client.model, "solar-pro3")
        self.assertEqual(client.base_url, "https://api.upstage.ai/v1")
        self.assertTrue(client.enabled)

    def test_upstage_does_not_inherit_xai_key(self) -> None:
        with patch.dict(
            os.environ,
            {"MONTHLY_LLM_PROVIDER": "upstage", "XAI_API_KEY": "xai-key"},
            clear=True,
        ):
            client = MonthlyReportClient.from_env()

        self.assertIsNone(client.api_key)
        self.assertFalse(client.enabled)

    def test_disabled_when_provider_unknown(self) -> None:
        with patch.dict(
            os.environ,
            {"MONTHLY_LLM_PROVIDER": "nope", "MONTHLY_LLM_API_KEY": "some-key"},
            clear=True,
        ):
            client = MonthlyReportClient.from_env()

        self.assertFalse(client.enabled)

    def test_missing_key_disables_client(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            client = MonthlyReportClient.from_env()

        self.assertEqual(client.provider, "xai")
        self.assertFalse(client.enabled)
