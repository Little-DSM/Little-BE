from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import MentoringApplication, MentoringMatch, MentoringPost, MentoringReview, User
from app.schemas.review import MentorReviewItem, MentorReviewSummaryResponse, RatingDistribution
from app.schemas.user import MentorDetailResponse
from app.services.dto import MentorQueryDTO


class _MentorMetrics:
    def __init__(self, db: Session):
        self.db = db

    def get_rating_stats(self, mentor_id: int) -> tuple[float | None, int]:
        stmt = select(
            func.avg(MentoringReview.rating),
            func.count(MentoringReview.id),
        ).where(MentoringReview.mentor_id == mentor_id)
        avg_value, count_value = self.db.execute(stmt).one()
        rating_count = int(count_value or 0)
        rating_average = round(float(avg_value), 2) if avg_value is not None else None
        return rating_average, rating_count

    def get_distribution(self, mentor_id: int, total_reviews: int) -> RatingDistribution:
        if total_reviews == 0:
            return RatingDistribution(
                one_star=0,
                two_star=0,
                three_star=0,
                four_star=0,
                five_star=0,
            )

        stmt = (
            select(MentoringReview.rating, func.count(MentoringReview.id))
            .where(MentoringReview.mentor_id == mentor_id)
            .group_by(MentoringReview.rating)
        )
        counts = {rating: int(count) for rating, count in self.db.execute(stmt).all()}

        def percent(score: int) -> int:
            return round((counts.get(score, 0) / total_reviews) * 100)

        return RatingDistribution(
            one_star=percent(1),
            two_star=percent(2),
            three_star=percent(3),
            four_star=percent(4),
            five_star=percent(5),
        )

    def get_review_items(self, mentor_id: int) -> list[MentorReviewItem]:
        stmt = (
            select(MentoringReview, MentoringPost)
            .join(MentoringMatch, MentoringMatch.id == MentoringReview.match_id)
            .join(MentoringPost, MentoringPost.id == MentoringMatch.post_id)
            .where(MentoringReview.mentor_id == mentor_id)
            .order_by(MentoringReview.created_at.desc())
        )
        rows = self.db.execute(stmt).all()
        items: list[MentorReviewItem] = []
        for review, post in rows:
            items.append(
                MentorReviewItem(
                    review_id=review.id,
                    rating=review.rating,
                    created_at=review.created_at,
                    post_id=post.id,
                    post_title=post.title,
                    reviewer_nickname=self._anonymous_nickname(review.mentee_id),
                    comment=review.comment,
                )
            )
        return items

    def _anonymous_nickname(self, user_id: int) -> str:
        animals = ["고라니", "토끼", "다람쥐", "사슴", "펭귄", "여우", "수달", "고양이"]
        return f"익명의 {animals[user_id % len(animals)]}"


def _get_mentor_or_404(db: Session, mentor_id: int) -> User:
    mentor = db.get(User, mentor_id)
    if mentor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="멘토를 찾을 수 없습니다",
        )
    return mentor


class GetMentorDetailService:
    def __init__(self, db: Session):
        self.db = db
        self.metrics = _MentorMetrics(db)

    def execute(self, dto: MentorQueryDTO) -> MentorDetailResponse:
        mentor = _get_mentor_or_404(self.db, dto.mentor_id)

        stmt = select(func.count(MentoringApplication.id)).where(
            MentoringApplication.mentor_id == dto.mentor_id
        )
        application_count = int(self.db.scalar(stmt) or 0)
        rating_average, rating_count = self.metrics.get_rating_stats(dto.mentor_id)

        return MentorDetailResponse(
            id=mentor.id,
            name=mentor.name,
            email=mentor.email,
            contact=mentor.contact,
            major=mentor.major,
            tech_stack=mentor.tech_stack,
            profile_image=mentor.profile_image,
            rating_average=rating_average,
            rating_count=rating_count,
            application_count=application_count,
        )


class GetMentorReviewsService:
    def __init__(self, db: Session):
        self.db = db
        self.metrics = _MentorMetrics(db)

    def execute(self, dto: MentorQueryDTO) -> MentorReviewSummaryResponse:
        _get_mentor_or_404(self.db, dto.mentor_id)
        rating_average, total_reviews = self.metrics.get_rating_stats(dto.mentor_id)
        distribution = self.metrics.get_distribution(dto.mentor_id, total_reviews)
        reviews = self.metrics.get_review_items(dto.mentor_id)

        return MentorReviewSummaryResponse(
            mentor_id=dto.mentor_id,
            average_rating=rating_average,
            total_reviews=total_reviews,
            distribution=distribution,
            reviews=reviews,
        )
