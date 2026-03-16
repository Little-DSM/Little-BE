from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "인증이 필요합니다",
            }
        }
    )

    detail: str = Field(..., description="에러 메시지")
