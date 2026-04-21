from datetime import datetime, timezone
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.config import get_google_oauth_settings
from app.auth.jwt import (
    create_access_token,
    create_oauth_state_token,
    create_refresh_token,
    decode_refresh_token,
    verify_oauth_state_token,
)
from app.models import RefreshToken, SocialAccount, User


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_google_oauth_settings()

    def get_google_authorization_url(
        self,
        frontend_redirect_uri: str | None = None,
    ) -> tuple[str, str]:
        self._validate_google_settings()
        resolved_frontend_redirect_uri = self._resolve_frontend_redirect_uri(frontend_redirect_uri)
        state = create_oauth_state_token(resolved_frontend_redirect_uri)
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

    def login_with_google_code(self, code: str, state: str) -> dict[str, str]:
        _, tokens = self._login_with_google_code_internal(code, state)
        return tokens

    def login_with_google_code_for_frontend_redirect(
        self,
        code: str,
        state: str,
    ) -> tuple[dict[str, str], str]:
        frontend_redirect_uri, tokens = self._login_with_google_code_internal(code, state)
        return tokens, frontend_redirect_uri

    def _login_with_google_code_internal(
        self,
        code: str,
        state: str,
    ) -> tuple[str, dict[str, str]]:
        self._validate_google_settings()
        frontend_redirect_uri = self._validate_state(state)
        token_payload = self._exchange_code_for_tokens(code)
        id_token_value = token_payload.get("id_token")
        if not id_token_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google 토큰 응답에 id_token 이 없습니다",
            )
        tokens = self.login_with_google_id_token(id_token_value)
        return frontend_redirect_uri, tokens

    def login_with_google_id_token(self, id_token_value: str) -> dict[str, str]:
        self._validate_google_settings()
        claims = self._verify_google_id_token(id_token_value)
        user = self._find_or_create_user(claims)
        return self.issue_token_pair(user.id)

    def issue_token_pair(self, user_id: int) -> dict[str, str]:
        token_id = uuid4().hex
        refresh_token = create_refresh_token(str(user_id), token_id)
        refresh_claims = decode_refresh_token(refresh_token)
        refresh_jti = str(refresh_claims["jti"])
        refresh_exp = int(refresh_claims["exp"])
        refresh_token_row = RefreshToken(
            token_id=refresh_jti,
            user_id=user_id,
            expires_at=datetime.fromtimestamp(
                refresh_exp,
                tz=timezone.utc,
            ),
        )
        self.db.add(refresh_token_row)
        self.db.commit()

        access_token = create_access_token(str(user_id))
        return {"access_token": access_token, "refresh_token": refresh_token}

    def refresh_access_token(self, raw_refresh_token: str) -> dict[str, str]:
        claims = self._validate_refresh_token_record(raw_refresh_token)
        self._revoke_token_by_jti(str(claims["jti"]))
        return self.issue_token_pair(int(claims["sub"]))

    def logout(self, user_id: int, raw_refresh_token: str) -> None:
        claims = self._validate_refresh_token_record(raw_refresh_token)
        if int(claims["sub"]) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="다른 사용자의 refresh token 은 로그아웃할 수 없습니다",
            )
        self._revoke_token_by_jti(str(claims["jti"]))

    def _validate_google_settings(self) -> None:
        if not self.settings.client_id or not self.settings.client_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth 설정이 누락되었습니다",
            )

    def _validate_state(self, state: str) -> str:
        try:
            frontend_redirect_uri = verify_oauth_state_token(state)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않은 OAuth state 입니다",
            ) from None
        return self._resolve_frontend_redirect_uri(frontend_redirect_uri)

    def _resolve_frontend_redirect_uri(self, frontend_redirect_uri: str | None) -> str:
        candidate = (frontend_redirect_uri or self.settings.frontend_redirect_uri).strip()
        if not candidate:
            candidate = self.settings.frontend_redirect_uri

        if candidate not in self.settings.allowed_frontend_redirect_uris:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="허용되지 않은 프론트엔드 리다이렉트 URI 입니다",
            )
        return candidate

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
            if claims.get("email") and not social_account.user.email:
                social_account.user.email = str(claims["email"])
                self.db.commit()
                self.db.refresh(social_account.user)
            return social_account.user

        name = str(claims.get("name") or "Google User")
        email = claims.get("email")
        picture = claims.get("picture")

        user = User(
            name=name,
            email=str(email) if email else None,
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

    def _validate_refresh_token_record(self, raw_refresh_token: str) -> dict[str, str | int]:
        try:
            claims = decode_refresh_token(raw_refresh_token)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않거나 만료된 refresh token 입니다",
            ) from None

        stmt = select(RefreshToken).where(RefreshToken.token_id == str(claims["jti"]))
        refresh_token_row = self.db.scalar(stmt)
        if refresh_token_row is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않거나 만료된 refresh token 입니다",
            )
        if refresh_token_row.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이미 로그아웃된 refresh token 입니다",
            )
        expires_at = refresh_token_row.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않거나 만료된 refresh token 입니다",
            )
        return claims

    def _revoke_token_by_jti(self, token_id: str) -> None:
        stmt = select(RefreshToken).where(RefreshToken.token_id == token_id)
        refresh_token_row = self.db.scalar(stmt)
        if refresh_token_row is None:
            return
        refresh_token_row.revoked_at = datetime.now(timezone.utc)
        self.db.commit()
