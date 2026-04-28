from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserSummary(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "김멘티",
                "major": "컴퓨터공학",
            }
        },
    )

    id: int = Field(..., description="사용자 ID")
    name: str = Field(..., description="작성자 이름")
    major: str = Field(..., description="작성자 전공")


class MentorApplicationSummary(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 2,
                "name": "박멘토",
                "major": "소프트웨어공학",
                "tech_stack": "Python, Django, FastAPI",
                "profile_image": "https://example.com/images/mentor-a.png",
            }
        },
    )

    id: int = Field(..., description="멘토 사용자 ID")
    name: str = Field(..., description="멘토 이름")
    major: str = Field(..., description="멘토 전공")
    tech_stack: str | None = Field(default=None, description="멘토 기술 스택")
    profile_image: str | None = Field(default=None, description="멘토 프로필 이미지 URL")


class MentorDetailResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 2,
                "name": "박멘토",
                "email": "mentor-a@example.com",
                "contact": "010-2222-2222",
                "major": "소프트웨어공학",
                "tech_stack": "Python, Django, FastAPI",
                "profile_image": "https://example.com/images/mentor-a.png",
                "rating_average": 4.5,
                "rating_count": 6,
                "application_count": 3,
            }
        },
    )

    id: int = Field(..., description="멘토 사용자 ID")
    name: str = Field(..., description="멘토 이름")
    email: str | None = Field(default=None, description="멘토 이메일")
    contact: str | None = Field(default=None, description="멘토 연락처")
    major: str = Field(..., description="멘토 전공")
    tech_stack: str | None = Field(default=None, description="멘토 기술 스택")
    profile_image: str | None = Field(default=None, description="멘토 프로필 이미지 URL")
    rating_average: float | None = Field(default=None, description="멘토 평균 별점")
    rating_count: int = Field(..., description="멘토 별점 개수")
    application_count: int = Field(..., description="해당 멘토의 전체 지원 횟수")


class MyPageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "김멘티",
                "email": "mentee@example.com",
                "introduction": "백엔드 개발자로 성장하고 싶은 멘티입니다.",
                "profile_image": "https://example.com/images/mentee.png",
                "major": "컴퓨터공학",
                "rating_average": 4.8,
                "rating_count": 10,
            }
        },
    )

    id: int = Field(..., description="사용자 ID")
    name: str = Field(..., description="이름")
    email: str | None = Field(default=None, description="이메일")
    introduction: str | None = Field(default=None, description="자기소개")
    profile_image: str | None = Field(default=None, description="프로필 이미지 URL")
    major: str = Field(..., description="전공")
    rating_average: float | None = Field(default=None, description="내 평균 별점")
    rating_count: int = Field(..., description="내 별점 개수")


class MyPageUpdateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "김멘티",
                "introduction": "백엔드 개발자로 성장하고 싶은 멘티입니다.",
                "profile_image": "https://example.com/images/my-profile.png",
                "major": "컴퓨터공학",
            }
        }
    )

    name: str = Field(..., description="수정할 이름", min_length=1)
    introduction: str | None = Field(default=None, description="수정할 자기소개")
    profile_image: str | None = Field(default=None, description="수정할 프로필 이미지 URL")
    major: str = Field(..., description="수정할 전공", min_length=1)


class MentoringProgressItem(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "post_id": 1,
                "title": "React가 알고 싶어요!",
                "major": "Frontend",
                "mentor_id": 2,
                "mentor_name": "박멘토",
                "mentor_contact": "010-3000-2000",
                "status": "IN_PROGRESS",
                "selected_at": "2026-04-06T11:00:00",
                "completed_at": None,
            }
        }
    )

    post_id: int = Field(..., description="멘토링 게시글 ID")
    title: str = Field(..., description="멘토링 게시글 제목")
    major: str = Field(..., description="멘토링 게시글 전공")
    mentor_id: int = Field(..., description="확정된 멘토 ID")
    mentor_name: str = Field(..., description="확정된 멘토 이름")
    mentor_contact: str = Field(..., description="확정된 멘토 연락처(미등록 시 기본 문구)")
    status: Literal["IN_PROGRESS", "COMPLETED"] = Field(..., description="멘토링 진행 상태")
    selected_at: datetime = Field(..., description="멘토 확정 시각")
    completed_at: datetime | None = Field(
        default=None,
        description="멘토링 완료 시각(리뷰 작성 시점)",
    )


class MentoringProgressListResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "post_id": 1,
                        "title": "React가 알고 싶어요!",
                        "major": "Frontend",
                        "mentor_id": 2,
                        "mentor_name": "박멘토",
                        "mentor_contact": "010-3000-2000",
                        "status": "IN_PROGRESS",
                        "selected_at": "2026-04-06T11:00:00",
                        "completed_at": None,
                    }
                ]
            }
        }
    )

    items: list[MentoringProgressItem] = Field(..., description="내 멘토링 진행 목록")


class MyPostListItem(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "post_id": 12,
                "title": "리액트에 대해 알려주세요!",
                "image_url": "https://example.com/images/react-post.png",
                "major": "Frontend",
                "author_name": "오찬영",
                "created_at": "2026-04-28T11:00:00",
                "view_count": 0,
            }
        }
    )

    post_id: int = Field(..., description="게시글 ID")
    title: str = Field(..., description="게시글 제목")
    image_url: str | None = Field(default=None, description="게시글 이미지 URL")
    major: str = Field(..., description="멘토링 전공")
    author_name: str = Field(..., description="작성자 이름")
    created_at: datetime = Field(..., description="게시글 작성 시각")
    view_count: int = Field(default=0, description="조회수(현재 기본값 0)")


class MyPostListResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_count": 2,
                "items": [
                    {
                        "post_id": 12,
                        "title": "리액트에 대해 알려주세요!",
                        "image_url": "https://example.com/images/react-post.png",
                        "major": "Frontend",
                        "author_name": "오찬영",
                        "created_at": "2026-04-28T11:00:00",
                        "view_count": 0,
                    }
                ],
            }
        }
    )

    total_count: int = Field(..., description="내 게시글 총 개수")
    items: list[MyPostListItem] = Field(..., description="내 게시글 목록")
