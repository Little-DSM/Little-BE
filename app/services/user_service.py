from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import MentoringApplication, User
from app.schemas.user import MentorDetailResponse, MyPageUpdateRequest


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

        return MentorDetailResponse(
            id=user.id,
            name=user.name,
            contact=user.contact,
            major=user.major,
            tech_stack=user.tech_stack,
            profile_image=user.profile_image,
            application_count=application_count,
        )

    def update_my_profile(self, user: User, payload: MyPageUpdateRequest) -> User:
        user.name = payload.name.strip()
        user.introduction = payload.introduction.strip() if payload.introduction else None
        user.profile_image = payload.profile_image.strip() if payload.profile_image else None
        user.major = payload.major.strip()
        self.db.commit()
        self.db.refresh(user)
        return user
