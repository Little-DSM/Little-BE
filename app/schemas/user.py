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
