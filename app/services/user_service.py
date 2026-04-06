from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import MentoringApplication, MentoringMatch, MentoringPost, MentoringReview, User
from app.schemas.review import MentorReviewItem, MentorReviewSummaryResponse, RatingDistribution
from app.schemas.user import MentorDetailResponse, MyPageResponse, MyPageUpdateRequest


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_mentor_detail(self, mentor_id: int) -> MentorDetailResponse:
        user = self.db.get(User, mentor_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="멘토를 찾을 수 없습니다",
            )

        stmt = select(func.count(MentoringApplication.id)).where(
            MentoringApplication.mentor_id == mentor_id
        )
        application_count = int(self.db.scalar(stmt) or 0)
        rating_average, rating_count = self._get_rating_stats(mentor_id)

        return MentorDetailResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            contact=user.contact,
            major=user.major,
            tech_stack=user.tech_stack,
            profile_image=user.profile_image,
            rating_average=rating_average,
            rating_count=rating_count,
            application_count=application_count,
        )

    def get_my_profile(self, user: User) -> MyPageResponse:
        rating_average, rating_count = self._get_rating_stats(user.id)
        return MyPageResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            introduction=user.introduction,
            profile_image=user.profile_image,
            major=user.major,
            rating_average=rating_average,
            rating_count=rating_count,
        )

    def update_my_profile(self, user: User, payload: MyPageUpdateRequest) -> MyPageResponse:
        user.name = payload.name.strip()
        user.introduction = payload.introduction.strip() if payload.introduction else None
        user.profile_image = payload.profile_image.strip() if payload.profile_image else None
        user.major = payload.major.strip()
        self.db.commit()
        self.db.refresh(user)
        return self.get_my_profile(user)

    def _get_rating_stats(self, mentor_id: int) -> tuple[float | None, int]:
        stmt = select(
            func.avg(MentoringReview.rating),
            func.count(MentoringReview.id),
        ).where(MentoringReview.mentor_id == mentor_id)
        avg_value, count_value = self.db.execute(stmt).one()
        rating_count = int(count_value or 0)
        rating_average = round(float(avg_value), 2) if avg_value is not None else None
        return rating_average, rating_count

    def get_mentor_review_summary(self, mentor_id: int) -> MentorReviewSummaryResponse:
        mentor = self.db.get(User, mentor_id)
        if mentor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="멘토를 찾을 수 없습니다",
            )

        rating_average, total_reviews = self._get_rating_stats(mentor_id)
        distribution = self._get_distribution(mentor_id, total_reviews)
        reviews = self._get_review_items(mentor_id)

        return MentorReviewSummaryResponse(
            mentor_id=mentor_id,
            average_rating=rating_average,
            total_reviews=total_reviews,
            distribution=distribution,
            reviews=reviews,
        )

    def _get_distribution(self, mentor_id: int, total_reviews: int) -> RatingDistribution:
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

    def _get_review_items(self, mentor_id: int) -> list[MentorReviewItem]:
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
