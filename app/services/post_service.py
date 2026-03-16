from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import MentoringApplication, MentoringPost, User
from app.schemas.post import MentoringPostCreate, MentoringPostUpdate


class PostService:
    def __init__(self, db: Session):
        self.db = db

    def create_post(self, payload: MentoringPostCreate, author: User) -> MentoringPost:
        post = MentoringPost(
            title=payload.title,
            description=payload.description,
            major=payload.major,
            author_id=author.id,
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return self.get_post(post.id)

    def list_posts(self) -> list[MentoringPost]:
        stmt = select(MentoringPost).order_by(MentoringPost.created_at.desc())
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
