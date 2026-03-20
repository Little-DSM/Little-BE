from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.config import get_google_oauth_settings
from app.auth.jwt import create_access_token, create_oauth_state_token, verify_oauth_state_token
from app.models import SocialAccount, User


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_google_oauth_settings()

    def get_google_authorization_url(self) -> tuple[str, str]:
        self._validate_google_settings()
        state = create_oauth_state_token()
        params = {
            "client_id": self.settings.client_id,
            "redirect_uri": self.settings.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return url, state

    def login_with_google_code(self, code: str, state: str) -> str:
        self._validate_google_settings()
        self._validate_state(state)
        token_payload = self._exchange_code_for_tokens(code)
        id_token_value = token_payload.get("id_token")
        if not id_token_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google 토큰 응답에 id_token 이 없습니다",
            )
        return self.login_with_google_id_token(id_token_value)

    def login_with_google_id_token(self, id_token_value: str) -> str:
        self._validate_google_settings()
        claims = self._verify_google_id_token(id_token_value)
        user = self._find_or_create_user(claims)
        return create_access_token(str(user.id))

    def _validate_google_settings(self) -> None:
        if not self.settings.client_id or not self.settings.client_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth 설정이 누락되었습니다",
            )

    def _validate_state(self, state: str) -> None:
        try:
            verify_oauth_state_token(state)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않은 OAuth state 입니다",
            ) from None

    def _exchange_code_for_tokens(self, code: str) -> dict[str, str]:
        payload = {
            "code": code,
            "client_id": self.settings.client_id,
            "client_secret": self.settings.client_secret,
            "redirect_uri": self.settings.redirect_uri,
            "grant_type": "authorization_code",
        }
        try:
            response = httpx.post(
                "https://oauth2.googleapis.com/token",
                data=payload,
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google OAuth code 교환에 실패했습니다",
            ) from None
        return response.json()

    def _verify_google_id_token(self, id_token_value: str) -> dict[str, str]:
        try:
            claims = id_token.verify_oauth2_token(
                id_token_value,
                google_requests.Request(),
                audience=self.settings.client_id,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 Google ID Token 입니다",
            ) from None

        sub = claims.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google ID Token의 sub 클레임이 없습니다",
            )
        return claims

    def _find_or_create_user(self, claims: dict[str, str]) -> User:
        google_sub = str(claims["sub"])
        stmt = select(SocialAccount).where(
            SocialAccount.provider == "google",
            SocialAccount.provider_user_id == google_sub,
        )
        social_account = self.db.scalar(stmt)
        if social_account:
            return social_account.user

        name = str(claims.get("name") or "Google User")
        email = claims.get("email")
        picture = claims.get("picture")

        user = User(
            name=name,
            major="미정",
            tech_stack=None,
            profile_image=picture,
        )
        self.db.add(user)
        self.db.flush()

        social_account = SocialAccount(
            provider="google",
            provider_user_id=google_sub,
            email=str(email) if email else None,
            user_id=user.id,
        )
        self.db.add(social_account)
        self.db.commit()
        self.db.refresh(user)
        return user
