from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

SECRET_KEY = "dev-secret-key-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 14
OAUTH_STATE_EXPIRE_MINUTES = 10


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "type": "access", "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("유효하지 않거나 만료된 토큰입니다") from exc

    subject = payload.get("sub")
    if not subject or payload.get("type") != "access":
        raise ValueError("유효하지 않거나 만료된 토큰입니다")

    return {"sub": str(subject)}


def create_refresh_token(subject: str, token_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "jti": token_id,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_refresh_token(token: str) -> dict[str, str | int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("유효하지 않거나 만료된 refresh token 입니다") from exc

    subject = payload.get("sub")
    token_id = payload.get("jti")
    exp = payload.get("exp")
    if not subject or not token_id or payload.get("type") != "refresh" or not isinstance(exp, int):
        raise ValueError("유효하지 않거나 만료된 refresh token 입니다")
    return {"sub": str(subject), "jti": str(token_id), "exp": exp}


def create_oauth_state_token() -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=OAUTH_STATE_EXPIRE_MINUTES)
    payload = {
        "sub": "google_oauth_state",
        "type": "oauth_state",
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_oauth_state_token(token: str) -> None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("유효하지 않은 OAuth state 입니다") from exc

    if payload.get("type") != "oauth_state":
        raise ValueError("유효하지 않은 OAuth state 입니다")
