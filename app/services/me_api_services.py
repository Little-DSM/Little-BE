from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.models import MentoringMatch, MentoringPost, MentoringReview, PostRole, User
from app.schemas.user import (
    MentoringProgressItem,
    MentoringProgressListResponse,
    MyPageResponse,
    MyPostListItem,
    MyPostListResponse,
)
from app.services.dto import MyMentoringProgressQueryDTO, MyPostsQueryDTO, MyProfileUpdateDTO


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )
    return user


def _get_rating_stats(db: Session, mentor_id: int) -> tuple[float | None, int]:
    stmt = select(
        func.avg(MentoringReview.rating),
        func.count(MentoringReview.id),
    ).where(MentoringReview.mentor_id == mentor_id)
    avg_value, count_value = db.execute(stmt).one()
    rating_count = int(count_value or 0)
    rating_average = round(float(avg_value), 2) if avg_value is not None else None
    return rating_average, rating_count


class GetMyProfileService:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, user_id: int) -> MyPageResponse:
        user = _get_user_or_404(self.db, user_id)
        rating_average, rating_count = _get_rating_stats(self.db, user.id)
        return MyPageResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            contact=user.contact,
            introduction=user.introduction,
            profile_image=user.profile_image,
            major=user.major,
            rating_average=rating_average,
            rating_count=rating_count,
        )


class UpdateMyProfileService:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, dto: MyProfileUpdateDTO) -> MyPageResponse:
        user = _get_user_or_404(self.db, dto.user_id)
        user.name = dto.name.strip()
        user.contact = dto.contact.strip() if dto.contact else None
        user.introduction = dto.introduction.strip() if dto.introduction else None
        user.profile_image = dto.profile_image.strip() if dto.profile_image else None
        user.major = dto.major.strip()
        self.db.commit()
        self.db.refresh(user)
        return GetMyProfileService(self.db).execute(user.id)


class GetMyMentoringProgressService:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, dto: MyMentoringProgressQueryDTO) -> MentoringProgressListResponse:
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
                    MentoringPost.author_id == dto.user_id,
                    MentoringMatch.mentor_id == dto.user_id,
                )
            )
            .order_by(MentoringMatch.selected_at.desc())
        )
        if dto.role_filter == "mentee":
            stmt = stmt.where(
                or_(
                    and_(
                        MentoringPost.role == PostRole.MENTEE,
                        MentoringPost.author_id == dto.user_id,
                    ),
                    and_(
                        MentoringPost.role == PostRole.MENTOR,
                        MentoringMatch.mentor_id == dto.user_id,
                    ),
                )
            )
        if dto.role_filter == "mentor":
            stmt = stmt.where(
                or_(
                    and_(
                        MentoringPost.role == PostRole.MENTEE,
                        MentoringMatch.mentor_id == dto.user_id,
                    ),
                    and_(
                        MentoringPost.role == PostRole.MENTOR,
                        MentoringPost.author_id == dto.user_id,
                    ),
                )
            )

        rows = self.db.execute(stmt).all()
        items: list[MentoringProgressItem] = []

        for match, post, mentor, author, review in rows:
            is_completed = review is not None
            progress_status = "COMPLETED" if is_completed else "IN_PROGRESS"
            if dto.status_filter == "completed" and not is_completed:
                continue
            if dto.status_filter == "in_progress" and is_completed:
                continue

            if post.role == PostRole.MENTEE:
                resolved_mentor = mentor
                resolved_mentee = author
            elif post.role == PostRole.MENTOR:
                resolved_mentor = author
                resolved_mentee = mentor
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="게시글 role 값이 올바르지 않습니다",
                )

            is_mentee = dto.user_id == resolved_mentee.id
            counterpart = resolved_mentor if is_mentee else resolved_mentee

            items.append(
                MentoringProgressItem(
                    post_id=post.id,
                    title=post.title,
                    major=post.major,
                    mentor_id=resolved_mentor.id,
                    mentor_name=resolved_mentor.name,
                    mentor_contact=resolved_mentor.contact or "연락처 미등록",
                    my_role="MENTEE" if is_mentee else "MENTOR",
                    counterpart_id=counterpart.id,
                    counterpart_name=counterpart.name,
                    counterpart_contact=counterpart.contact or "연락처 미등록",
                    status=progress_status,
                    selected_at=match.selected_at,
                    completed_at=review.created_at if review else None,
                )
            )

        return MentoringProgressListResponse(items=items)


class GetMyPostsService:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, dto: MyPostsQueryDTO) -> MyPostListResponse:
        user = _get_user_or_404(self.db, dto.user_id)
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
                role=post.role,
                author_name=user.name,
                created_at=post.created_at,
                view_count=0,
            )
            for post in posts
        ]
        return MyPostListResponse(total_count=len(items), items=items)
