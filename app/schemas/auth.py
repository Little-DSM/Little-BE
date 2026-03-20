from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
            }
        }
    )

    user_id: int = Field(..., description="로그인할 사용자 ID", examples=[1])


class TokenResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.sample-token",
                "token_type": "bearer",
            }
        }
    )

    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = Field(default="bearer", description="인증 타입")


class GoogleAuthUrlResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
                "state": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.sample-state",
            }
        }
    )

    authorization_url: str = Field(..., description="사용자를 보낼 구글 OAuth 인증 URL")
    state: str = Field(..., description="OAuth CSRF 방지용 state 토큰")


class GoogleOAuthCallbackRequest(BaseModel):
    code: str = Field(..., description="Google callback에서 받은 authorization code")
    state: str = Field(..., description="Google callback에서 받은 state")


class GoogleIdTokenRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE2....",
            }
        }
    )

    id_token: str = Field(..., description="Google Sign-In에서 받은 ID Token")
