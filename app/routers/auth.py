from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.database.session import get_db
from app.models import User
from app.schemas.auth import (
    GoogleAuthUrlResponse,
    GoogleIdTokenRequest,
    GoogleOAuthCallbackRequest,
    LoginRequest,
    TokenResponse,
)
from app.schemas.common import ErrorResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="데모 로그인",
    description=(
        "샘플 사용자 ID로 로그인하여 JWT 액세스 토큰을 발급합니다. "
        "Swagger 우측 상단 `Authorize` 버튼에서 `Bearer {token}` 형식으로 사용합니다."
    ),
    responses={
        200: {"description": "로그인 성공 및 JWT 발급"},
        404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"},
    },
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.get(
    "/google/login",
    response_model=GoogleAuthUrlResponse,
    summary="Google OAuth 로그인 URL 발급",
    description="프론트엔드가 사용자를 구글 로그인 화면으로 보낼 URL과 state를 발급합니다.",
    responses={
        200: {"description": "OAuth 인증 URL 발급 성공"},
        500: {"model": ErrorResponse, "description": "Google OAuth 설정 누락"},
    },
)
def google_login_url(db: Session = Depends(get_db)) -> GoogleAuthUrlResponse:
    auth_service = AuthService(db)
    authorization_url, state = auth_service.get_google_authorization_url()
    return GoogleAuthUrlResponse(authorization_url=authorization_url, state=state)


@router.post(
    "/google/callback",
    response_model=TokenResponse,
    summary="Google OAuth callback 처리",
    description=(
        "Google에서 전달한 authorization code와 state를 받아 검증하고 "
        "서비스용 JWT 액세스 토큰을 발급합니다."
    ),
    responses={
        200: {"description": "Google 로그인 성공"},
        400: {"model": ErrorResponse, "description": "유효하지 않은 code/state"},
        401: {"model": ErrorResponse, "description": "유효하지 않은 Google ID Token"},
        500: {"model": ErrorResponse, "description": "Google OAuth 설정 누락"},
    },
)
def google_callback(
    payload: GoogleOAuthCallbackRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    token = AuthService(db).login_with_google_code(payload.code, payload.state)
    return TokenResponse(access_token=token)


@router.post(
    "/google/token",
    response_model=TokenResponse,
    summary="Google ID Token 로그인",
    description=(
        "프론트엔드에서 Google Sign-In으로 받은 id_token을 서버에 전달하면 "
        "검증 후 서비스 JWT 토큰을 발급합니다."
    ),
    responses={
        200: {"description": "Google 로그인 성공"},
        401: {"model": ErrorResponse, "description": "유효하지 않은 Google ID Token"},
        500: {"model": ErrorResponse, "description": "Google OAuth 설정 누락"},
    },
)
def google_id_token_login(
    payload: GoogleIdTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    token = AuthService(db).login_with_google_id_token(payload.id_token)
    return TokenResponse(access_token=token)
