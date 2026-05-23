import json
import os
import unittest
from datetime import date
from unittest.mock import Mock, patch

from app.schemas.ai_retention import ActionCalendarLLMResponse, TimingSignal
from app.services.chart_engine import NatalProfile
from app.services.llm_retention_client import LLMRetentionClient


class LLMRetentionClientTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = NatalProfile(
            sun_sign="Sagittarius",
            moon_sign="Scorpio",
            rising_sign="Cancer",
            dominant_element="water",
            dominant_element_label="물",
            focus_areas=("관계", "커리어"),
            base_scores={"career": 4.0, "money": 3.0, "love": 5.0, "risk": 2.0},
        )
        self.analysis = Mock()
        self.analysis.year = 2026
        self.analysis.month = 5
        self.analysis.title = "관계와 커리어 흐름"
        self.analysis.top_theme_label = "관계"
        self.analysis.intensity_score = 7
        self.signal = TimingSignal(
            date=date(2026, 5, 10),
            totalScore=2.0,
            categoryScores={"career": 1.2, "love": 0.8},
            positiveSignals=["커리어 흐름이 살아납니다."],
            negativeSignals=[],
        )

    def test_from_env_selects_deepseek_provider(self) -> None:
        with patch.dict(
            os.environ,
            {
                "LLM_RETENTION_PROVIDER": "deepseek",
                "LLM_RETENTION_API_KEY": "test-key",
                "LLM_RETENTION_MODEL": "deepseek-v4-pro",
            },
            clear=False,
        ):
            client = LLMRetentionClient.from_env()

        self.assertEqual(client.provider, "deepseek")
        self.assertTrue(client.enabled)
        self.assertEqual(client.model, "deepseek-v4-pro")

    def test_from_env_selects_gemma_provider(self) -> None:
        with patch.dict(
            os.environ,
            {
                "LLM_RETENTION_PROVIDER": "gemma",
                "GEMMA_API_KEY": "test-key",
            },
            clear=False,
        ):
            client = LLMRetentionClient.from_env()

        self.assertEqual(client.provider, "gemma")
        self.assertTrue(client.enabled)
        self.assertEqual(client.model, "unsloth/gemma-4-E2B-it-GGUF:UD-Q4_K_XL")
        self.assertEqual(client.base_url, "https://gemma.donggyu.link")

    def test_xai_response_parser_reads_responses_output_text(self) -> None:
        client = LLMRetentionClient(provider="xai", api_key="test-key", model="test-model", timeout_seconds=5)
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "output": [{"content": [{"text": json.dumps({"days": [self._day_payload()]}, ensure_ascii=False)}]}]
        }

        with patch("app.services.llm_retention_client.httpx.post", return_value=response) as post:
            result = client.generate_action_calendar(
                profile=self.profile,
                analysis=self.analysis,
                signals=[self.signal],
                fallback_days=[],
            )

        self.assertIsInstance(result, ActionCalendarLLMResponse)
        self.assertEqual(result.days[0].title, "연락이 풀리는 날")
        self.assertIn("/responses", str(post.call_args.args[0]))

    def test_deepseek_response_parser_reads_chat_completion_content(self) -> None:
        client = LLMRetentionClient(provider="deepseek", api_key="test-key", model="deepseek-v4-pro", timeout_seconds=5)
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({"days": [self._day_payload()]}, ensure_ascii=False)}}]
        }

        with patch("app.services.llm_retention_client.httpx.post", return_value=response) as post:
            result = client.generate_action_calendar(
                profile=self.profile,
                analysis=self.analysis,
                signals=[self.signal],
                fallback_days=[],
            )

        self.assertIsInstance(result, ActionCalendarLLMResponse)
        self.assertEqual(result.days[0].score, 8)
        self.assertIn("/chat/completions", str(post.call_args.args[0]))

    def test_gemma_response_parser_reads_openai_chat_completion_content(self) -> None:
        client = LLMRetentionClient(
            provider="gemma",
            api_key="test-key",
            model="unsloth/gemma-4-E2B-it-GGUF:UD-Q4_K_XL",
            timeout_seconds=5,
            base_url="https://gemma.donggyu.link",
        )
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({"days": [self._day_payload()]}, ensure_ascii=False)}}]
        }

        with patch("app.services.llm_retention_client.httpx.post", return_value=response) as post:
            result = client.generate_action_calendar(
                profile=self.profile,
                analysis=self.analysis,
                signals=[self.signal],
                fallback_days=[],
            )

        self.assertIsInstance(result, ActionCalendarLLMResponse)
        self.assertEqual(result.days[0].score, 8)
        self.assertEqual(post.call_args.args[0], "https://gemma.donggyu.link/v1/chat/completions")
        request_payload = post.call_args.kwargs["json"]
        self.assertEqual(request_payload["model"], "unsloth/gemma-4-E2B-it-GGUF:UD-Q4_K_XL")
        self.assertNotIn("response_format", request_payload)

    def test_invalid_provider_disables_client(self) -> None:
        client = LLMRetentionClient(provider="none", api_key="test-key", model="test-model", timeout_seconds=5)

        self.assertFalse(client.enabled)

    def _day_payload(self) -> dict:
        return {
            "date": "2026-05-10",
            "score": 8,
            "tone": "supportive",
            "title": "연락이 풀리는 날",
            "action": "오전에 중요한 연락을 보낸다.",
            "avoid": "일정을 과하게 늘리지 않는다.",
            "reason": "관계와 커리어 신호가 함께 좋다.",
            "categories": ["career", "love"],
        }
