from fastapi import FastAPI

app = FastAPI(
    title="littleDSM API",
    version="0.1.0",
    description="Base FastAPI application for littleDSM.",
)


@app.get("/", tags=["health"])
async def read_root() -> dict[str, str]:
    return {"message": "littleDSM FastAPI server is running"}


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
