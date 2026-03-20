from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

SECRET_KEY = "dev-secret-key-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
OAUTH_STATE_EXPIRE_MINUTES = 10


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("유효하지 않거나 만료된 토큰입니다") from exc

    subject = payload.get("sub")
    if not subject:
        raise ValueError("유효하지 않거나 만료된 토큰입니다")

    return {"sub": str(subject)}


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
