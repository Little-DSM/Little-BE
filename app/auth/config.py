import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GoogleOAuthSettings:
    client_id: str
    client_secret: str
    redirect_uri: str
    frontend_redirect_uri: str
    allowed_frontend_redirect_uris: tuple[str, ...]


def get_google_oauth_settings() -> GoogleOAuthSettings:
    default_allowed = (
        "https://little-fe.vercel.app/main",
        "http://localhost:5173/main",
    )
    raw_allowed = os.getenv("GOOGLE_ALLOWED_FRONTEND_REDIRECT_URIS", "")
    if raw_allowed.strip():
        allowed_uris = tuple(uri.strip() for uri in raw_allowed.split(",") if uri.strip())
    else:
        allowed_uris = default_allowed

    frontend_redirect_uri = os.getenv(
        "GOOGLE_FRONTEND_REDIRECT_URI",
        "http://localhost:5173/main",
    ).strip()
    if not frontend_redirect_uri:
        frontend_redirect_uri = "http://localhost:5173/main"
    if frontend_redirect_uri not in allowed_uris:
        allowed_uris = (*allowed_uris, frontend_redirect_uri)

    return GoogleOAuthSettings(
        client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8001/auth/google/callback"),
        frontend_redirect_uri=frontend_redirect_uri,
        allowed_frontend_redirect_uris=allowed_uris,
    )
