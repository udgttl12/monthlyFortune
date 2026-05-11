import unittest

from fastapi.testclient import TestClient

from app.main import app


class AIRetentionApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.base_params = {
            "birthDate": "1990-01-01",
            "birthTime": "09:00",
            "city": "Seoul",
            "countryCode": "KR",
            "year": "2026",
            "month": "5",
            "timezone": "Asia/Seoul",
        }

    def test_action_calendar_endpoint_returns_days(self) -> None:
        response = self.client.get("/api/ai-retention/action-calendar", params=self.base_params)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["year"], 2026)
        self.assertEqual(payload["month"], 5)
        self.assertGreaterEqual(len(payload["days"]), 28)
        self.assertIn("llmEnhanced", payload)

    def test_daily_brief_endpoint_returns_target_date(self) -> None:
        response = self.client.get(
            "/api/ai-retention/daily-brief",
            params={**self.base_params, "targetDate": "2026-05-10"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["date"], "2026-05-10")
        self.assertIn("headline", payload)

    def test_coach_endpoint_requires_question(self) -> None:
        response = self.client.post("/api/ai-retention/coach", json=self.base_params)

        self.assertEqual(response.status_code, 422)
