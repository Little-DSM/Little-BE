from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased

from app.models import MentoringApplication, MentoringMatch, MentoringPost, MentoringReview, User
from app.schemas.review import MentorReviewItem, MentorReviewSummaryResponse, RatingDistribution
from app.schemas.user import (
    MentorDetailResponse,
    MentoringProgressItem,
    MentoringProgressListResponse,
    MyPageResponse,
    MyPageUpdateRequest,
    MyPostListItem,
    MyPostListResponse,
)


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

    def get_my_mentoring_progress(
        self,
        user: User,
        status_filter: str = "all",
        role_filter: str = "all",
    ) -> MentoringProgressListResponse:
        mentor_user = aliased(User)
        author_user = aliased(User)

        stmt = (
            select(MentoringMatch, MentoringPost, mentor_user, author_user, MentoringReview)
            .join(MentoringPost, MentoringPost.id == MentoringMatch.post_id)
            .join(mentor_user, mentor_user.id == MentoringMatch.mentor_id)
            .join(author_user, author_user.id == MentoringPost.author_id)
            .outerjoin(MentoringReview, MentoringReview.match_id == MentoringMatch.id)
            .where(
                or_(
                    MentoringPost.author_id == user.id,
                    MentoringMatch.mentor_id == user.id,
                )
            )
            .order_by(MentoringMatch.selected_at.desc())
        )
        if role_filter == "mentee":
            stmt = stmt.where(MentoringPost.author_id == user.id)
        if role_filter == "mentor":
            stmt = stmt.where(MentoringMatch.mentor_id == user.id)

        rows = self.db.execute(stmt).all()
        items: list[MentoringProgressItem] = []

        for match, post, mentor, author, review in rows:
            is_completed = review is not None
            status = "COMPLETED" if is_completed else "IN_PROGRESS"
            if status_filter == "completed" and not is_completed:
                continue
            if status_filter == "in_progress" and is_completed:
                continue
            is_mentee = post.author_id == user.id
            counterpart = mentor if is_mentee else author

            items.append(
                MentoringProgressItem(
                    post_id=post.id,
                    title=post.title,
                    major=post.major,
                    mentor_id=mentor.id,
                    mentor_name=mentor.name,
                    mentor_contact=mentor.contact or "연락처 미등록",
                    my_role="MENTEE" if is_mentee else "MENTOR",
                    counterpart_id=counterpart.id,
                    counterpart_name=counterpart.name,
                    counterpart_contact=counterpart.contact or "연락처 미등록",
                    status=status,
                    selected_at=match.selected_at,
                    completed_at=review.created_at if review else None,
                )
            )

        return MentoringProgressListResponse(items=items)

    def get_my_posts(self, user: User) -> MyPostListResponse:
        stmt = (
            select(MentoringPost)
            .where(MentoringPost.author_id == user.id)
            .order_by(MentoringPost.created_at.desc())
        )
        posts = list(self.db.scalars(stmt).all())

        items = [
            MyPostListItem(
                post_id=post.id,
                title=post.title,
                image_url=post.image_url,
                major=post.major,
                author_name=user.name,
                created_at=post.created_at,
                view_count=0,
            )
            for post in posts
        ]
        return MyPostListResponse(total_count=len(items), items=items)

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
