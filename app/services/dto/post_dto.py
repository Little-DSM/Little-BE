from dataclasses import dataclass

from app.models import PostRole


@dataclass(frozen=True)
class PostCreateDTO:
    author_id: int
    title: str
    image_url: str | None
    description: str | None
    major: str
    role: PostRole


@dataclass(frozen=True)
class PostListQueryDTO:
    keyword: str | None = None
    major: str | None = None
    role: PostRole | None = None


@dataclass(frozen=True)
class PostUpdateDTO:
    post_id: int
    user_id: int
    title: str
    image_url: str | None
    description: str | None
    major: str


@dataclass(frozen=True)
class PostOwnershipDTO:
    post_id: int
    user_id: int


@dataclass(frozen=True)
class PostApplyDTO:
    post_id: int
    applicant_id: int


@dataclass(frozen=True)
class PostSelectMentorDTO:
    post_id: int
    selector_id: int
    mentor_id: int


@dataclass(frozen=True)
class PostReviewUpsertDTO:
    post_id: int
    reviewer_id: int
    rating: int
    comment: str | None
