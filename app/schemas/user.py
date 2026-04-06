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
                "contact": "010-2222-2222",
                "major": "소프트웨어공학",
                "tech_stack": "Python, Django, FastAPI",
                "profile_image": "https://example.com/images/mentor-a.png",
                "application_count": 3,
            }
        },
    )

    id: int = Field(..., description="멘토 사용자 ID")
    name: str = Field(..., description="멘토 이름")
    contact: str | None = Field(default=None, description="멘토 연락처")
    major: str = Field(..., description="멘토 전공")
    tech_stack: str | None = Field(default=None, description="멘토 기술 스택")
    profile_image: str | None = Field(default=None, description="멘토 프로필 이미지 URL")
    application_count: int = Field(..., description="해당 멘토의 전체 지원 횟수")


class MyPageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "김멘티",
                "introduction": "백엔드 개발자로 성장하고 싶은 멘티입니다.",
                "profile_image": "https://example.com/images/mentee.png",
                "major": "컴퓨터공학",
            }
        },
    )

    id: int = Field(..., description="사용자 ID")
    name: str = Field(..., description="이름")
    introduction: str | None = Field(default=None, description="자기소개")
    profile_image: str | None = Field(default=None, description="프로필 이미지 URL")
    major: str = Field(..., description="전공")


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
