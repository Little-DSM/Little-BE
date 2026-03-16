from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

SECRET_KEY = "dev-secret-key-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


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
