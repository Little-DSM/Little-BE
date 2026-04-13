# Little-BE

멘토링 매칭 서비스 백엔드(FastAPI) 프로젝트입니다.

## 1. 실행 전 준비

- Python 3.11+

## 2. 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## 3. 환경변수 설정

프로젝트 루트(`/Users/bagtaesu/Desktop/git/littleDSM`)에 `.env` 파일을 만들고 아래 값을 채웁니다.

```env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:8001/auth/google/callback
GOOGLE_FRONTEND_REDIRECT_URI=http://127.0.0.1:3000/oauth/callback

JWT_SECRET_KEY=your-jwt-secret-key
ACCESS_TOKEN_EXPIRE=120
REFRESH_TOKEN_EXPIRE=7

# 선택: 외부 DB/캐시 사용 시
DATABASE_URL=sqlite:///./mentoring.db
REDIS_URL=redis://127.0.0.1:6379/0
```

- `ACCESS_TOKEN_EXPIRE`: 분(minute) 단위
- `REFRESH_TOKEN_EXPIRE`: 일(day) 단위

## 4. 서버 실행

```bash
uvicorn app.main:app --reload --port 8001 --env-file .env
```

- API Base URL: `http://127.0.0.1:8001`
- Swagger: `http://127.0.0.1:8001/docs`
- ReDoc: `http://127.0.0.1:8001/redoc`

## 5. API 사용 흐름 (필수)

### 5-1. 로그인

실서비스 기준으로는 Google 로그인 사용:

- `POST /auth/google/token`

응답으로 아래 토큰 쌍을 받습니다.

- `access_token`
- `refresh_token`

### 5-2. 인증이 필요한 API 호출

`Authorization` 헤더에 아래 형식으로 `access_token`을 넣습니다.

```text
Authorization: Bearer <access_token>
```

### 5-3. 토큰 만료 시 재발급

- `POST /auth/refresh`
- body에 `refresh_token` 전달
- 새 `access_token`, `refresh_token` 쌍을 다시 받습니다.

### 5-4. 로그아웃

- `POST /auth/logout`
- 헤더: `Bearer access_token`
- body: `refresh_token`
- 해당 refresh token 세션이 폐기됩니다.

### 5-5. 멘토링 핵심 기능 흐름

1. 멘티가 게시글 생성: `POST /posts`
2. 멘토가 게시글 지원: `POST /posts/{post_id}/apply`
3. 멘티가 지원자 목록 확인: `GET /posts/{post_id}/applications`
4. 멘티가 멘토 확정: `POST /posts/{post_id}/select-mentor`
5. 멘티가 확정 결과 확인: `GET /posts/{post_id}/selected-mentor`

추가 조회:

- 게시글 전체/검색: `GET /posts`, `GET /posts?keyword=&major=`
- 멘토 상세(연락처 포함): `GET /mentors/{mentor_id}`

## 부가사항

### API 계약 문서

- [docs/API_CONTRACT.md](/Users/bagtaesu/Desktop/git/littleDSM/docs/API_CONTRACT.md)

### 테스트

```bash
pytest
```

### 린트

```bash
ruff check .
```

### 참고

- `.env` 파일은 `.gitignore`에 포함되어 있어 Git에 올라가지 않습니다.
- Deployment heartbeat update: 2026-04-13 (google-env-rollout)
