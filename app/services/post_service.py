from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import MentoringApplication, MentoringMatch, MentoringPost, MentoringReview, User
from app.schemas.post import MentoringPostCreate, MentoringPostUpdate


class PostService:
    def __init__(self, db: Session):
        self.db = db

    def create_post(self, payload: MentoringPostCreate, author: User) -> MentoringPost:
        post = MentoringPost(
            title=payload.title,
            image_url=payload.image_url,
            description=payload.description,
            major=payload.major,
            author_id=author.id,
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return self.get_post(post.id)

    def list_posts(
        self,
        keyword: str | None = None,
        major: str | None = None,
    ) -> list[MentoringPost]:
        stmt = select(MentoringPost)
        if keyword and keyword.strip():
            pattern = f"%{keyword.strip()}%"
            stmt = stmt.where(
                or_(
                    MentoringPost.title.like(pattern),
                    MentoringPost.description.like(pattern),
                    MentoringPost.major.like(pattern),
                )
            )
        if major and major.strip():
            stmt = stmt.where(MentoringPost.major == major.strip())
        stmt = stmt.order_by(MentoringPost.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def get_post(self, post_id: int) -> MentoringPost:
        stmt = (
            select(MentoringPost)
            .options(joinedload(MentoringPost.author))
            .where(MentoringPost.id == post_id)
        )
        post = self.db.scalar(stmt)
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다",
            )
        return post

    def update_post(self, post_id: int, payload: MentoringPostUpdate, user: User) -> MentoringPost:
        post = self._get_owned_post(post_id, user.id)
        post.title = payload.title
        post.image_url = payload.image_url
        post.description = payload.description
        post.major = payload.major
        self.db.commit()
        self.db.refresh(post)
        return self.get_post(post.id)

    def delete_post(self, post_id: int, user: User) -> None:
        post = self._get_owned_post(post_id, user.id)
        self.db.delete(post)
        self.db.commit()

    def get_applications(self, post_id: int, user: User) -> list[User]:
        post = self.get_post(post_id)
        if post.author_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="지원자 목록은 작성자만 조회할 수 있습니다",
            )

        stmt = (
            select(User)
            .join(MentoringApplication, MentoringApplication.mentor_id == User.id)
            .where(MentoringApplication.post_id == post_id)
            .order_by(User.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def apply_to_post(self, post_id: int, mentor: User) -> MentoringApplication:
        post = self.get_post(post_id)
        if post.author_id == mentor.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="본인 게시글에는 지원할 수 없습니다",
            )

        exists_stmt = select(MentoringApplication).where(
            MentoringApplication.post_id == post_id,
            MentoringApplication.mentor_id == mentor.id,
        )
        if self.db.scalar(exists_stmt):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 지원한 게시글입니다",
            )

        application = MentoringApplication(post_id=post_id, mentor_id=mentor.id)
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    def select_mentor(self, post_id: int, mentor_id: int, user: User) -> MentoringMatch:
        self._get_owned_post(post_id, user.id)

        application_stmt = select(MentoringApplication).where(
            MentoringApplication.post_id == post_id,
            MentoringApplication.mentor_id == mentor_id,
        )
        if self.db.scalar(application_stmt) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="해당 멘토는 이 게시글에 지원하지 않았습니다",
            )

        mentor = self.db.get(User, mentor_id)
        if mentor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="멘토를 찾을 수 없습니다",
            )

        match_stmt = select(MentoringMatch).where(MentoringMatch.post_id == post_id)
        match = self.db.scalar(match_stmt)
        if match is None:
            match = MentoringMatch(
                post_id=post_id,
                mentor_id=mentor_id,
                selected_by_id=user.id,
            )
            self.db.add(match)
        else:
            match.mentor_id = mentor_id
            match.selected_by_id = user.id

        self.db.commit()
        self.db.refresh(match)
        return match

    def get_selected_mentor(self, post_id: int, user: User) -> MentoringMatch:
        post = self._get_owned_post(post_id, user.id)
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

    def create_or_update_review(
        self,
        post_id: int,
        user: User,
        rating: int,
        comment: str | None,
    ) -> MentoringReview:
        post = self._get_owned_post(post_id, user.id)
        match_stmt = select(MentoringMatch).where(MentoringMatch.post_id == post.id)
        match = self.db.scalar(match_stmt)
        if match is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="멘토 확정 후에만 별점을 남길 수 있습니다",
            )

        review_stmt = select(MentoringReview).where(MentoringReview.match_id == match.id)
        review = self.db.scalar(review_stmt)
        if review is None:
            review = MentoringReview(
                match_id=match.id,
                mentor_id=match.mentor_id,
                mentee_id=user.id,
                rating=rating,
                comment=comment.strip() if comment else None,
            )
            self.db.add(review)
        else:
            review.rating = rating
            review.comment = comment.strip() if comment else None

        self.db.commit()
        self.db.refresh(review)
        return review

    def _get_owned_post(self, post_id: int, user_id: int) -> MentoringPost:
        post = self.db.get(MentoringPost, post_id)
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다",
            )
        if post.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="게시글 작성자만 수정 또는 삭제할 수 있습니다",
            )
        return post
