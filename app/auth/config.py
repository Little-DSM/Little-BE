import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GoogleOAuthSettings:
    client_id: str
    client_secret: str
    redirect_uri: str
    frontend_redirect_uri: str


def get_google_oauth_settings() -> GoogleOAuthSettings:
    return GoogleOAuthSettings(
        client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8001/auth/google/callback"),
        frontend_redirect_uri=os.getenv("GOOGLE_FRONTEND_REDIRECT_URI", "http://127.0.0.1:3000/oauth/callback"),
    )
