from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import MentoringApplication, MentoringReview, User
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
