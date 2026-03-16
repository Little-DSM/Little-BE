from pydantic import BaseModel, ConfigDict


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    major: str


class MentorApplicationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    major: str
    tech_stack: str | None = None
    profile_image: str | None = None
