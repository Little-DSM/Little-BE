from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.user import MentorApplicationSummary, UserSummary


def _validate_required_text(value: str, message: str) -> str:
    if not value or not value.strip():
        raise ValueError(message)
    return value.strip()


class MentoringPostCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "백엔드 멘토링을 받고 싶어요",
                "image_url": "https://example.com/images/mentoring-request.png",
                "description": "JWT 인증과 SQLAlchemy 구조 설계에 대한 멘토링이 필요합니다.",
                "major": "컴퓨터공학",
            }
        }
    )

    title: str = Field(..., description="멘토링 게시글 제목")
    image_url: str | None = Field(default=None, description="멘토링 게시글 대표 이미지 URL")
    description: str | None = Field(default=None, description="멘토링 상세 설명")
    major: str = Field(..., description="원하는 멘토 전공")

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _validate_required_text(value, "제목을 입력해주세요")

    @field_validator("major")
    @classmethod
    def validate_major(cls, value: str) -> str:
        return _validate_required_text(value, "전공을 입력해주세요")


class MentoringPostUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "FastAPI 구조 멘토링을 받고 싶어요",
                "image_url": "https://example.com/images/updated-mentoring-request.png",
                "description": "프로젝트 구조와 예외 처리 방식을 같이 검토받고 싶습니다.",
                "major": "소프트웨어공학",
            }
        }
    )

    title: str = Field(..., description="수정할 게시글 제목")
    image_url: str | None = Field(default=None, description="수정할 게시글 대표 이미지 URL")
    description: str | None = Field(default=None, description="수정할 게시글 상세 설명")
    major: str = Field(..., description="수정할 원하는 멘토 전공")

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _validate_required_text(value, "제목을 입력해주세요")

    @field_validator("major")
    @classmethod
    def validate_major(cls, value: str) -> str:
        return _validate_required_text(value, "전공을 입력해주세요")


class MentoringPostListItem(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "백엔드 멘토링이 필요해요",
                "image_url": "https://example.com/images/post-sample.png",
                "description": "FastAPI 프로젝트 구조와 인증 설계를 배우고 싶습니다.",
                "major": "컴퓨터공학",
                "created_at": "2026-03-16T14:00:00",
            }
        },
    )

    id: int = Field(..., description="게시글 ID")
    title: str = Field(..., description="게시글 제목")
    image_url: str | None = Field(default=None, description="게시글 대표 이미지 URL")
    description: str | None = Field(default=None, description="게시글 상세 설명")
    major: str = Field(..., description="원하는 전공")
    created_at: datetime = Field(..., description="게시글 생성 시각")


class MentoringPostDetail(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "백엔드 멘토링이 필요해요",
                "image_url": "https://example.com/images/post-sample.png",
                "description": "FastAPI 프로젝트 구조와 인증 설계를 배우고 싶습니다.",
                "major": "컴퓨터공학",
                "created_at": "2026-03-16T14:00:00",
                "author": {
                    "id": 1,
                    "name": "김멘티",
                    "major": "컴퓨터공학",
                },
            }
        },
    )

    id: int = Field(..., description="게시글 ID")
    title: str = Field(..., description="게시글 제목")
    image_url: str | None = Field(default=None, description="게시글 대표 이미지 URL")
    description: str | None = Field(default=None, description="게시글 상세 설명")
    major: str = Field(..., description="원하는 전공")
    created_at: datetime = Field(..., description="게시글 생성 시각")
    author: UserSummary = Field(..., description="게시글 작성자 정보")


class MentorApplicationsResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "post_id": 1,
                "mentors": [
                    {
                        "id": 2,
                        "name": "박멘토",
                        "major": "소프트웨어공학",
                        "tech_stack": "Python, Django, FastAPI",
                        "profile_image": "https://example.com/images/mentor-a.png",
                    }
                ],
            }
        }
    )

    post_id: int = Field(..., description="게시글 ID")
    mentors: list[MentorApplicationSummary] = Field(..., description="지원한 멘토 목록")


class MentorSelectRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mentor_id": 2,
            }
        }
    )

    mentor_id: int = Field(..., description="확정할 멘토 사용자 ID")


class MentorSelectResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "post_id": 1,
                "mentor": {
                    "id": 2,
                    "name": "박멘토",
                    "major": "소프트웨어공학",
                    "tech_stack": "Python, Django, FastAPI",
                    "profile_image": "https://example.com/images/mentor-a.png",
                },
                "selected_at": "2026-04-01T10:30:00",
            }
        }
    )

    post_id: int = Field(..., description="게시글 ID")
    mentor: MentorApplicationSummary = Field(..., description="확정된 멘토")
    selected_at: datetime = Field(..., description="멘토 확정 시각")


class ReviewCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rating": 5,
                "comment": "설명이 정말 꼼꼼하고 도움이 많이 됐어요.",
            }
        }
    )

    rating: int = Field(..., ge=1, le=5, description="별점(1~5)")
    comment: str | None = Field(default=None, description="리뷰 코멘트")


class ReviewResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "post_id": 1,
                "mentor_id": 2,
                "mentee_id": 1,
                "rating": 5,
                "comment": "설명이 정말 꼼꼼하고 도움이 많이 됐어요.",
                "created_at": "2026-04-06T12:00:00",
            }
        }
    )

    post_id: int
    mentor_id: int
    mentee_id: int
    rating: int
    comment: str | None = None
    created_at: datetime
