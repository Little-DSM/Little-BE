from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database.init_db import init_db
from app.routers.auth import router as auth_router
from app.routers.posts import router as posts_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Little-BE Mentoring API",
    version="1.0.0",
    description="멘토링 매칭 서비스를 위한 FastAPI REST API 서버",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(posts_router)


@app.get("/", tags=["health"])
async def read_root() -> dict[str, str]:
    return {"message": "Little-BE mentoring API server is running"}


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
