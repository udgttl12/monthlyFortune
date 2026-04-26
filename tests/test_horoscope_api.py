import unittest

from fastapi.testclient import TestClient

from app.main import app


class HoroscopeApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def setUp(self) -> None:
        self.base_params = {
            "birthDate": "1988-12-06",
            "birthTime": "19:59",
            "city": "Busan",
            "countryCode": "KR",
            "timezone": "Asia/Seoul",
            "year": "2026",
        }

    def test_yearly_missing_birth_details_returns_400(self) -> None:
        response = self.client.get("/api/horoscope/yearly", params={"year": "2026"})

        self.assertEqual(response.status_code, 400)

    def test_yearly_returns_all_twelve_months(self) -> None:
        response = self.client.get("/api/horoscope/yearly", params=self.base_params)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["year"], 2026)
        self.assertEqual(len(payload["months"]), 12)
        self.assertIn("profileSummary", payload)
        self.assertIn("luckyWindow", payload["months"][0])
        self.assertIn("cautionWindow", payload["months"][0])

    def test_monthly_includes_dates_evidence_and_llm_flag(self) -> None:
        response = self.client.get(
            "/api/horoscope/monthly",
            params={**self.base_params, "month": "4"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["year"], 2026)
        self.assertEqual(payload["month"], 4)
        self.assertIn("summary", payload)
        self.assertIn("sections", payload)
        self.assertEqual(len(payload["luckyDates"]), 3)
        self.assertEqual(len(payload["cautionDates"]), 3)
        self.assertGreaterEqual(len(payload["evidence"]), 1)
        self.assertIn("llmEnhanced", payload)
