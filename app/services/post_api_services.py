from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models import (
    MentoringApplication,
    MentoringMatch,
    MentoringPost,
    MentoringReview,
    PostRole,
    User,
)
from app.services.dto import (
    PostApplyDTO,
    PostCreateDTO,
    PostListQueryDTO,
    PostOwnershipDTO,
    PostReviewUpsertDTO,
    PostSelectMentorDTO,
    PostUpdateDTO,
)


class _PostAccess:
    def __init__(self, db: Session):
        self.db = db

    def get_post(self, post_id: int, include_author: bool = False) -> MentoringPost:
        stmt = select(MentoringPost).where(MentoringPost.id == post_id)
        if include_author:
            stmt = stmt.options(joinedload(MentoringPost.author))
        post = self.db.scalar(stmt)
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다",
            )
        return post

    def get_owned_post(self, dto: PostOwnershipDTO) -> MentoringPost:
        post = self.db.get(MentoringPost, dto.post_id)
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다",
            )
        if post.author_id != dto.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="게시글 작성자만 수정 또는 삭제할 수 있습니다",
            )
        return post

    @staticmethod
    def resolve_participants(
        post: MentoringPost,
        match: MentoringMatch,
    ) -> tuple[int, int]:
        if post.role == PostRole.MENTEE:
            return post.author_id, match.mentor_id
        if post.role == PostRole.MENTOR:
            return match.mentor_id, post.author_id

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="게시글 role 값이 올바르지 않습니다",
        )

    def commit_or_raise_post_persist_error(self) -> None:
        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게시글 저장에 실패했습니다. 입력값 길이를 확인해주세요",
            ) from None


class CreatePostService:
    def __init__(self, db: Session):
        self.db = db
        self.access = _PostAccess(db)

    def execute(self, dto: PostCreateDTO) -> MentoringPost:
        post = MentoringPost(
            title=dto.title,
            image_url=dto.image_url,
            description=dto.description,
            major=dto.major,
            role=dto.role,
            author_id=dto.author_id,
        )
        self.db.add(post)
        self.access.commit_or_raise_post_persist_error()
        self.db.refresh(post)
        return self.access.get_post(post.id, include_author=True)


class ListPostsService:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, dto: PostListQueryDTO) -> list[MentoringPost]:
        stmt = select(MentoringPost)
        if dto.keyword and dto.keyword.strip():
            pattern = f"%{dto.keyword.strip()}%"
            stmt = stmt.where(
                or_(
                    MentoringPost.title.like(pattern),
                    MentoringPost.description.like(pattern),
                    MentoringPost.major.like(pattern),
                )
            )
        if dto.major and dto.major.strip():
            stmt = stmt.where(MentoringPost.major == dto.major.strip())
        if dto.role is not None:
            stmt = stmt.where(MentoringPost.role == dto.role)
        stmt = stmt.order_by(MentoringPost.created_at.desc())
        return list(self.db.scalars(stmt).all())


class GetPostService:
    def __init__(self, db: Session):
        self.access = _PostAccess(db)

    def execute(self, post_id: int) -> MentoringPost:
        return self.access.get_post(post_id, include_author=True)


class UpdatePostService:
    def __init__(self, db: Session):
        self.db = db
        self.access = _PostAccess(db)

    def execute(self, dto: PostUpdateDTO) -> MentoringPost:
        ownership = PostOwnershipDTO(post_id=dto.post_id, user_id=dto.user_id)
        post = self.access.get_owned_post(ownership)
        post.title = dto.title
        post.image_url = dto.image_url
        post.description = dto.description
        post.major = dto.major
        self.access.commit_or_raise_post_persist_error()
        self.db.refresh(post)
        return self.access.get_post(post.id, include_author=True)


class DeletePostService:
    def __init__(self, db: Session):
        self.db = db
        self.access = _PostAccess(db)

    def execute(self, dto: PostOwnershipDTO) -> None:
        post = self.access.get_owned_post(dto)
        self.db.delete(post)
        self.db.commit()


class GetPostApplicationsService:
    def __init__(self, db: Session):
        self.db = db
        self.access = _PostAccess(db)

    def execute(self, dto: PostOwnershipDTO) -> list[User]:
        post = self.access.get_post(dto.post_id)
        if post.author_id != dto.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="지원자 목록은 작성자만 조회할 수 있습니다",
            )

        stmt = (
            select(User)
            .join(MentoringApplication, MentoringApplication.mentor_id == User.id)
            .where(MentoringApplication.post_id == dto.post_id)
            .order_by(User.id.asc())
        )
        return list(self.db.scalars(stmt).all())


class ApplyToPostService:
    def __init__(self, db: Session):
        self.db = db
        self.access = _PostAccess(db)

    def execute(self, dto: PostApplyDTO) -> MentoringApplication:
        post = self.access.get_post(dto.post_id)
        if post.author_id == dto.applicant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="본인 게시글에는 지원할 수 없습니다",
            )

        exists_stmt = select(MentoringApplication).where(
            MentoringApplication.post_id == dto.post_id,
            MentoringApplication.mentor_id == dto.applicant_id,
        )
        if self.db.scalar(exists_stmt):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 지원한 게시글입니다",
            )

        application = MentoringApplication(post_id=dto.post_id, mentor_id=dto.applicant_id)
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application


class SelectMentorService:
    def __init__(self, db: Session):
        self.db = db
        self.access = _PostAccess(db)

    def execute(self, dto: PostSelectMentorDTO) -> MentoringMatch:
        self.access.get_owned_post(PostOwnershipDTO(post_id=dto.post_id, user_id=dto.selector_id))

        application_stmt = select(MentoringApplication).where(
            MentoringApplication.post_id == dto.post_id,
            MentoringApplication.mentor_id == dto.mentor_id,
        )
        if self.db.scalar(application_stmt) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="해당 멘토는 이 게시글에 지원하지 않았습니다",
            )

        mentor = self.db.get(User, dto.mentor_id)
        if mentor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="멘토를 찾을 수 없습니다",
            )

        match_stmt = select(MentoringMatch).where(MentoringMatch.post_id == dto.post_id)
        match = self.db.scalar(match_stmt)
        if match is None:
            match = MentoringMatch(
                post_id=dto.post_id,
                mentor_id=dto.mentor_id,
                selected_by_id=dto.selector_id,
            )
            self.db.add(match)
        else:
            match.mentor_id = dto.mentor_id
            match.selected_by_id = dto.selector_id

        self.db.commit()
        self.db.refresh(match)
        return match


class GetSelectedMentorService:
    def __init__(self, db: Session):
        self.db = db
        self.access = _PostAccess(db)

    def execute(self, dto: PostOwnershipDTO) -> MentoringMatch:
        post = self.access.get_owned_post(dto)
        match_stmt = (
            select(MentoringMatch)
            .options(joinedload(MentoringMatch.mentor))
            .where(MentoringMatch.post_id == post.id)
        )
        match = self.db.scalar(match_stmt)
        if match is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="아직 확정된 멘토가 없습니다",
            )
        return match


class UpsertPostReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.access = _PostAccess(db)

    def execute(self, dto: PostReviewUpsertDTO) -> MentoringReview:
        post = self.db.get(MentoringPost, dto.post_id)
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다",
            )

        match_stmt = select(MentoringMatch).where(MentoringMatch.post_id == post.id)
        match = self.db.scalar(match_stmt)
        if match is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="멘토 확정 후에만 별점을 남길 수 있습니다",
            )

        mentee_id, mentor_id = self.access.resolve_participants(post, match)
        if dto.reviewer_id != mentee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="멘티만 리뷰를 작성할 수 있습니다",
            )

        review_stmt = select(MentoringReview).where(MentoringReview.match_id == match.id)
        review = self.db.scalar(review_stmt)
        normalized_comment = dto.comment.strip() if dto.comment else None
        if review is None:
            review = MentoringReview(
                match_id=match.id,
                mentor_id=mentor_id,
                mentee_id=mentee_id,
                rating=dto.rating,
                comment=normalized_comment,
            )
            self.db.add(review)
        else:
            review.rating = dto.rating
            review.comment = normalized_comment

        self.db.commit()
        self.db.refresh(review)
        return review
