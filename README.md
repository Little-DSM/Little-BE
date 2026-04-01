# Little-BE

멘토링 매칭 서비스 백엔드(FastAPI) 프로젝트입니다.

## 요구 사항

- Python 3.11+

## 시작하기

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## 서버 실행

```bash
uvicorn app.main:app --reload --port 8001
```

- API: `http://127.0.0.1:8001`
- Swagger: `http://127.0.0.1:8001/docs`
- ReDoc: `http://127.0.0.1:8001/redoc`

## Google OAuth 설정

서버 실행 전에 아래 환경변수를 설정하세요.

```bash
export GOOGLE_CLIENT_ID="your-google-client-id"
export GOOGLE_CLIENT_SECRET="your-google-client-secret"
export GOOGLE_REDIRECT_URI="http://127.0.0.1:8001/auth/google/callback"
export GOOGLE_FRONTEND_REDIRECT_URI="http://127.0.0.1:3000/oauth/callback"
export JWT_SECRET_KEY="9f3a2c7e5b8d4a1c6f0e9b2d7a3c8e1f4b6d9a2c7e5f1b3a8c6d0e4f9a2b7c1d"
export ACCESS_TOKEN_EXPIRE="120"
export REFRESH_TOKEN_EXPIRE="7"
```

관련 인증 API:

- `GET /auth/google/login`
- `POST /auth/google/callback`
- `POST /auth/google/token`
- `POST /auth/refresh`
- `POST /auth/logout`

기본 로그인/Google 로그인 응답에는 `access_token`, `refresh_token`이 함께 내려옵니다.

## 테스트

```bash
pytest
```

## 린트

```bash
ruff check .
```
