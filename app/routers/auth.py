from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models import User
from app.schemas.auth import (
    AuthTokenPairResponse,
    GoogleAuthUrlResponse,
    GoogleIdTokenRequest,
    GoogleOAuthCallbackRequest,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
)
from app.schemas.common import ErrorResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=AuthTokenPairResponse,
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
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthTokenPairResponse:
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )

    tokens = AuthService(db).issue_token_pair(user.id)
    return AuthTokenPairResponse(**tokens)


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
    response_model=AuthTokenPairResponse,
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
) -> AuthTokenPairResponse:
    tokens = AuthService(db).login_with_google_code(payload.code, payload.state)
    return AuthTokenPairResponse(**tokens)


@router.post(
    "/google/token",
    response_model=AuthTokenPairResponse,
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
) -> AuthTokenPairResponse:
    tokens = AuthService(db).login_with_google_id_token(payload.id_token)
    return AuthTokenPairResponse(**tokens)


@router.post(
    "/refresh",
    response_model=AuthTokenPairResponse,
    summary="토큰 재발급",
    description="refresh token 으로 새로운 access token/refresh token 쌍을 재발급합니다.",
    responses={
        200: {"description": "토큰 재발급 성공"},
        401: {"model": ErrorResponse, "description": "유효하지 않거나 만료된 refresh token"},
    },
)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> AuthTokenPairResponse:
    tokens = AuthService(db).refresh_access_token(payload.refresh_token)
    return AuthTokenPairResponse(**tokens)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="로그아웃",
    description="현재 사용자 세션의 refresh token 을 폐기합니다.",
    responses={
        200: {"description": "로그아웃 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "다른 사용자 토큰으로 요청"},
    },
)
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LogoutResponse:
    AuthService(db).logout(current_user.id, payload.refresh_token)
    return LogoutResponse(message="로그아웃되었습니다")
