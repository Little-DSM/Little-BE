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
```

관련 인증 API:

- `GET /auth/google/login`
- `POST /auth/google/callback`
- `POST /auth/google/token`

## 테스트

```bash
pytest
```

## 린트

```bash
ruff check .
```
