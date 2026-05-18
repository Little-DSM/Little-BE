from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class MyProfileUpdateDTO:
    user_id: int
    name: str
    contact: str | None
    introduction: str | None
    profile_image: str | None
    major: str


@dataclass(frozen=True)
class MyMentoringProgressQueryDTO:
    user_id: int
    status_filter: Literal["all", "in_progress", "completed"] = "all"
    role_filter: Literal["all", "mentee", "mentor"] = "all"


@dataclass(frozen=True)
class MyPostsQueryDTO:
    user_id: int
