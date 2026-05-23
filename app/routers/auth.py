from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from app.schemas.auth import AuthRequest, AuthResponse, AuthUserResponse
from app.services.auth_service import AuthService, AuthServiceUnavailable

router = APIRouter(prefix="/api/auth", tags=["auth"])

auth_service = AuthService.from_env()


def _get_auth_service() -> AuthService:
    if auth_service is None:
        raise HTTPException(status_code=503, detail="회원 기능을 사용하려면 MariaDB 설정이 필요합니다.")
    return auth_service


@router.post("/signup", response_model=AuthResponse)
def signup(request: AuthRequest) -> AuthResponse:
    try:
        token, email = _get_auth_service().signup(request.email, request.password)
        return AuthResponse(token=token, email=email)
    except AuthServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
def login(request: AuthRequest) -> AuthResponse:
    try:
        token, email = _get_auth_service().login(request.email, request.password)
        return AuthResponse(token=token, email=email)
    except AuthServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me", response_model=AuthUserResponse)
def me(authorization: Optional[str] = Header(None)) -> AuthUserResponse:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        email = _get_auth_service().get_user_email(token)
    except AuthServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if email is None:
        raise HTTPException(status_code=401, detail="로그인이 만료되었거나 올바르지 않습니다.")

    return AuthUserResponse(email=email)
