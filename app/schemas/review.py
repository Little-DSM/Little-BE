from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RatingDistribution(BaseModel):
    one_star: int = Field(..., description="1점 비율(%)")
    two_star: int = Field(..., description="2점 비율(%)")
    three_star: int = Field(..., description="3점 비율(%)")
    four_star: int = Field(..., description="4점 비율(%)")
    five_star: int = Field(..., description="5점 비율(%)")


class MentorReviewItem(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "review_id": 12,
                "rating": 4,
                "created_at": "2026-10-10T09:00:00",
                "post_id": 3,
                "post_title": "React 멘토링 해주세요",
                "reviewer_nickname": "익명의 고라니",
                "comment": "코드리뷰가 꼼꼼해서 도움됐어요.",
            }
        }
    )

    review_id: int
    rating: int
    created_at: datetime
    post_id: int
    post_title: str
    reviewer_nickname: str
    comment: str | None = None


class MentorReviewSummaryResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mentor_id": 2,
                "average_rating": 3.2,
                "total_reviews": 300,
                "distribution": {
                    "one_star": 30,
                    "two_star": 10,
                    "three_star": 20,
                    "four_star": 40,
                    "five_star": 10,
                },
                "reviews": [],
            }
        }
    )

    mentor_id: int
    average_rating: float | None = None
    total_reviews: int
    distribution: RatingDistribution
    reviews: list[MentorReviewItem]
