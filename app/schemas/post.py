from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.user import MentorApplicationSummary, UserSummary


def _validate_required_text(value: str, message: str) -> str:
    if not value or not value.strip():
        raise ValueError(message)
    return value.strip()


class MentoringPostCreate(BaseModel):
    title: str
    description: str | None = None
    major: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _validate_required_text(value, "제목을 입력해주세요")

    @field_validator("major")
    @classmethod
    def validate_major(cls, value: str) -> str:
        return _validate_required_text(value, "전공을 입력해주세요")


class MentoringPostUpdate(BaseModel):
    title: str
    description: str | None = None
    major: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _validate_required_text(value, "제목을 입력해주세요")

    @field_validator("major")
    @classmethod
    def validate_major(cls, value: str) -> str:
        return _validate_required_text(value, "전공을 입력해주세요")


class MentoringPostListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    major: str
    created_at: datetime


class MentoringPostDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    major: str
    created_at: datetime
    author: UserSummary


class MentorApplicationsResponse(BaseModel):
    post_id: int
    mentors: list[MentorApplicationSummary]
