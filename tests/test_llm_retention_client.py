import json
import os
import unittest
from datetime import date
from unittest.mock import Mock, patch

import httpx

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

    def test_from_env_selects_upstage_provider(self) -> None:
        with patch.dict(
            os.environ,
            {
                "LLM_RETENTION_PROVIDER": "upstage",
                "UPSTAGE_API_KEY": "test-key",
            },
            clear=True,
        ):
            client = LLMRetentionClient.from_env()

        self.assertEqual(client.provider, "upstage")
        self.assertTrue(client.enabled)
        self.assertEqual(client.model, "solar-pro3")
        self.assertEqual(client.base_url, "https://api.upstage.ai/v1")
        self.assertIsNone(client.reasoning_effort)

    def test_from_env_upstage_ignores_gemma_base_url(self) -> None:
        # GEMMA_API_BASE_URL은 .env.production.example에 값이 채워져 있다.
        # provider 스코프가 없으면 upstage 요청이 gemma 호스트로 나간다.
        with patch.dict(
            os.environ,
            {
                "LLM_RETENTION_PROVIDER": "upstage",
                "UPSTAGE_API_KEY": "test-key",
                "GEMMA_API_BASE_URL": "https://gemma.donggyu.link",
                "GEMMA_API_KEY": "gemma-key",
            },
            clear=True,
        ):
            client = LLMRetentionClient.from_env()

        self.assertEqual(client.base_url, "https://api.upstage.ai/v1")
        self.assertEqual(client.api_key, "test-key")

    def test_from_env_gemma_still_uses_gemma_base_url(self) -> None:
        with patch.dict(
            os.environ,
            {
                "LLM_RETENTION_PROVIDER": "gemma",
                "GEMMA_API_KEY": "gemma-key",
                "GEMMA_API_BASE_URL": "https://gemma.example.test",
            },
            clear=True,
        ):
            client = LLMRetentionClient.from_env()

        self.assertEqual(client.base_url, "https://gemma.example.test")
        self.assertEqual(client.api_key, "gemma-key")

    def test_from_env_reads_upstage_reasoning_effort(self) -> None:
        with patch.dict(
            os.environ,
            {
                "LLM_RETENTION_PROVIDER": "upstage",
                "UPSTAGE_API_KEY": "test-key",
                "UPSTAGE_REASONING_EFFORT": "low",
            },
            clear=True,
        ):
            client = LLMRetentionClient.from_env()

        self.assertEqual(client.reasoning_effort, "low")

    def test_upstage_response_parser_reads_chat_completion_content(self) -> None:
        client = self._upstage_client()
        response = self._chat_completion_response(
            json.dumps({"days": [self._day_payload()]}, ensure_ascii=False)
        )

        with patch("app.services.llm_retention_client.httpx.post", return_value=response) as post:
            result = client.generate_action_calendar(
                profile=self.profile,
                analysis=self.analysis,
                signals=[self.signal],
                fallback_days=[],
            )

        self.assertIsInstance(result, ActionCalendarLLMResponse)
        self.assertEqual(result.days[0].score, 8)
        self.assertEqual(post.call_args.args[0], "https://api.upstage.ai/v1/chat/completions")

    def test_upstage_request_uses_flattened_json_schema(self) -> None:
        client = self._upstage_client()
        response = self._chat_completion_response(
            json.dumps({"days": [self._day_payload()]}, ensure_ascii=False)
        )

        with patch("app.services.llm_retention_client.httpx.post", return_value=response) as post:
            client.generate_action_calendar(
                profile=self.profile,
                analysis=self.analysis,
                signals=[self.signal],
                fallback_days=[],
            )

        response_format = post.call_args.kwargs["json"]["response_format"]
        self.assertEqual(response_format["type"], "json_schema")
        self.assertEqual(response_format["json_schema"]["name"], "action_calendar")
        self.assertIs(response_format["json_schema"]["strict"], True)
        self.assertNotIn("$ref", json.dumps(response_format["json_schema"]["schema"]))
        self.assertIs(response_format["json_schema"]["schema"]["additionalProperties"], False)

    def test_upstage_omits_reasoning_effort_by_default(self) -> None:
        client = self._upstage_client()
        response = self._chat_completion_response(
            json.dumps({"days": [self._day_payload()]}, ensure_ascii=False)
        )

        with patch("app.services.llm_retention_client.httpx.post", return_value=response) as post:
            client.generate_action_calendar(
                profile=self.profile,
                analysis=self.analysis,
                signals=[self.signal],
                fallback_days=[],
            )

        self.assertNotIn("reasoning_effort", post.call_args.kwargs["json"])

    def test_upstage_sends_reasoning_effort_when_configured(self) -> None:
        client = self._upstage_client(reasoning_effort="high")
        response = self._chat_completion_response(
            json.dumps({"days": [self._day_payload()]}, ensure_ascii=False)
        )

        with patch("app.services.llm_retention_client.httpx.post", return_value=response) as post:
            client.generate_action_calendar(
                profile=self.profile,
                analysis=self.analysis,
                signals=[self.signal],
                fallback_days=[],
            )

        self.assertEqual(post.call_args.kwargs["json"]["reasoning_effort"], "high")

    def test_upstage_appends_v1_to_base_url_without_it(self) -> None:
        client = self._upstage_client(base_url="https://api.upstage.ai")
        response = self._chat_completion_response(
            json.dumps({"days": [self._day_payload()]}, ensure_ascii=False)
        )

        with patch("app.services.llm_retention_client.httpx.post", return_value=response) as post:
            client.generate_action_calendar(
                profile=self.profile,
                analysis=self.analysis,
                signals=[self.signal],
                fallback_days=[],
            )

        self.assertEqual(post.call_args.args[0], "https://api.upstage.ai/v1/chat/completions")

    def test_upstage_reads_content_parts_array(self) -> None:
        client = self._upstage_client()
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "reasoning": "사용자는 행동 캘린더를 원한다.",
                        "content": [
                            {"text": json.dumps({"days": [self._day_payload()]}, ensure_ascii=False)}
                        ],
                    }
                }
            ]
        }

        with patch("app.services.llm_retention_client.httpx.post", return_value=response):
            result = client.generate_action_calendar(
                profile=self.profile,
                analysis=self.analysis,
                signals=[self.signal],
                fallback_days=[],
            )

        self.assertIsInstance(result, ActionCalendarLLMResponse)

    def test_upstage_returns_none_on_http_error(self) -> None:
        client = self._upstage_client()

        with patch(
            "app.services.llm_retention_client.httpx.post",
            side_effect=httpx.TimeoutException("timeout"),
        ):
            result = client.generate_action_calendar(
                profile=self.profile,
                analysis=self.analysis,
                signals=[self.signal],
                fallback_days=[],
            )

        self.assertIsNone(result)

    def test_upstage_returns_none_on_malformed_json(self) -> None:
        client = self._upstage_client()
        response = self._chat_completion_response("{not-json")

        with patch("app.services.llm_retention_client.httpx.post", return_value=response):
            result = client.generate_action_calendar(
                profile=self.profile,
                analysis=self.analysis,
                signals=[self.signal],
                fallback_days=[],
            )

        self.assertIsNone(result)

    def test_invalid_provider_disables_client(self) -> None:
        client = LLMRetentionClient(provider="none", api_key="test-key", model="test-model", timeout_seconds=5)

        self.assertFalse(client.enabled)

    def _upstage_client(self, **overrides) -> LLMRetentionClient:
        kwargs = {
            "provider": "upstage",
            "api_key": "test-key",
            "model": "solar-pro3",
            "timeout_seconds": 5,
            "base_url": "https://api.upstage.ai/v1",
        }
        kwargs.update(overrides)
        return LLMRetentionClient(**kwargs)

    def _chat_completion_response(self, content: str) -> Mock:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"choices": [{"message": {"content": content}}]}
        return response

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
