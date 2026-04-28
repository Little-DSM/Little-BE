from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.database.init_db import init_db
from app.database.session import SessionLocal
from app.redis_client import close_redis, get_redis_client, init_redis
from app.routers.auth import router as auth_router
from app.routers.me import router as me_router
from app.routers.mentors import router as mentors_router
from app.routers.posts import router as posts_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    init_redis()
    try:
        yield
    finally:
        close_redis()


app = FastAPI(
    title="Little-BE Mentoring API",
    version="1.0.0",
    description=(
        "멘티가 멘토링 요청 게시글을 작성하고 멘토 지원자를 관리할 수 있는 REST API입니다.\n\n"
        "인증 방법:\n"
        "1. `POST /auth/login` 으로 JWT 토큰을 발급받습니다.\n"
        "2. Swagger 우측 상단 `Authorize` 버튼에서 `Bearer <token>` 형식으로 입력합니다.\n"
        "3. 이후 `/posts` 하위 API를 호출합니다."
    ),
    lifespan=lifespan,
    contact={
        "name": "Little-BE API",
        "url": "https://github.com/Little-DSM/Little-BE",
    },
    openapi_tags=[
        {"name": "auth", "description": "JWT 토큰 발급, 데모 로그인, Google OAuth 인증 API"},
        {"name": "me", "description": "마이페이지 조회/수정 API"},
        {"name": "posts", "description": "멘토링 게시글 생성, 조회, 수정, 삭제 및 지원자 조회 API"},
        {"name": "mentors", "description": "멘토 상세 정보 조회 API"},
        {"name": "health", "description": "서버 상태 확인 API"},
    ],
)


def _resolve_field_name(loc: tuple[str | int, ...] | list[str | int]) -> str:
    field_map = {
        "title": "제목",
        "major": "전공",
        "description": "설명",
        "image_url": "이미지 URL",
        "user_id": "사용자 ID",
        "name": "이름",
        "rating": "별점",
        "code": "authorization code",
        "state": "state",
        "refresh_token": "refresh token",
        "id_token": "Google ID token",
        "frontend_redirect_uri": "프론트엔드 리다이렉트 URI",
    }
    for value in reversed(loc):
        if isinstance(value, str) and value not in {"body", "query", "path", "header"}:
            return field_map.get(value, value)
    return "요청값"


def _format_validation_message(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "요청값이 올바르지 않습니다"

    first_error = errors[0]
    message = str(first_error.get("msg", "요청값이 올바르지 않습니다"))
    location = first_error.get("loc", ())
    field_name = _resolve_field_name(location)

    if message.startswith("Value error, "):
        return message.replace("Value error, ", "", 1)

    if message == "Field required":
        return f"{field_name} 값을 입력해주세요"

    if message == "Input should be a valid integer":
        return f"{field_name}은(는) 정수 형식이어야 합니다"

    if message.startswith("Input should be less than or equal to "):
        limit = message.replace("Input should be less than or equal to ", "", 1)
        return f"{field_name}은(는) {limit} 이하로 입력해주세요"

    if message.startswith("Input should be greater than or equal to "):
        limit = message.replace("Input should be greater than or equal to ", "", 1)
        return f"{field_name}은(는) {limit} 이상으로 입력해주세요"

    if message == "JSON decode error":
        return "요청 본문 JSON 형식이 올바르지 않습니다"

    return message


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": _format_validation_message(exc)},
    )

allowed_origins = [
    "http://localhost:5173",
    "https://little-fe.vercel.app",
    "https://little-fe.vercel.app/",
    "https://little-orpin.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https://little-fe(-[a-z0-9-]+)?\.vercel\.app/?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(me_router)
app.include_router(posts_router)
app.include_router(mentors_router)


@app.get(
    "/",
    tags=["health"],
    summary="루트 헬스체크",
    description="서버가 실행 중인지 간단한 메시지로 확인합니다.",
)
async def read_root() -> dict[str, str]:
    return {"message": "Little-BE mentoring API server is running"}


@app.get(
    "/health",
    tags=["health"],
    summary="상세 헬스체크",
    description="API 서버의 기본 상태를 확인합니다.",
)
async def health_check() -> dict[str, str]:
    database = "ok"
    redis = "not_configured"

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        database = "error"

    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            redis_client.ping()
            redis = "ok"
        except Exception:
            redis = "error"

    status = "ok" if database == "ok" and redis != "error" else "degraded"
    return {"status": status, "database": database, "redis": redis}
