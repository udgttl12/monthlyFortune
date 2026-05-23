import unittest

from fastapi.testclient import TestClient

import app.routers.auth as auth_router
from app.main import app


class FakeAuthService:
    def signup(self, email: str, password: str):
        return "signup-token", email.strip().casefold()

    def login(self, email: str, password: str):
        if password != "correct-password":
            raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다.")
        return "login-token", email.strip().casefold()

    def get_user_email(self, token: str):
        return "user@example.com" if token == "login-token" else None


class AuthApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.original_service = auth_router.auth_service
        auth_router.auth_service = FakeAuthService()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        auth_router.auth_service = self.original_service

    def test_signup_returns_token(self) -> None:
        response = self.client.post(
            "/api/auth/signup",
            json={"email": "USER@example.com", "password": "strong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["token"], "signup-token")
        self.assertEqual(response.json()["email"], "user@example.com")

    def test_login_rejects_wrong_password(self) -> None:
        response = self.client.post(
            "/api/auth/login",
            json={"email": "user@example.com", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 401)

    def test_me_requires_valid_bearer_token(self) -> None:
        response = self.client.get("/api/auth/me", headers={"Authorization": "Bearer login-token"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "user@example.com")


if __name__ == "__main__":
    unittest.main()
