from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models import User
from app.schemas.post import (
    MentorApplicationsResponse,
    MentoringPostCreate,
    MentoringPostDetail,
    MentoringPostListItem,
    MentoringPostUpdate,
)
from app.schemas.user import MentorApplicationSummary
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", response_model=MentoringPostDetail, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: MentoringPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MentoringPostDetail:
    post = PostService(db).create_post(payload, current_user)
    return MentoringPostDetail.model_validate(post)


@router.get("", response_model=list[MentoringPostListItem])
def list_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MentoringPostListItem]:
    del current_user
    posts = PostService(db).list_posts()
    return [MentoringPostListItem.model_validate(post) for post in posts]


@router.get("/{post_id}", response_model=MentoringPostDetail)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MentoringPostDetail:
    del current_user
    post = PostService(db).get_post(post_id)
    return MentoringPostDetail.model_validate(post)


@router.patch("/{post_id}", response_model=MentoringPostDetail)
def update_post(
    post_id: int,
    payload: MentoringPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MentoringPostDetail:
    post = PostService(db).update_post(post_id, payload, current_user)
    return MentoringPostDetail.model_validate(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    PostService(db).delete_post(post_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{post_id}/applications", response_model=MentorApplicationsResponse)
def get_applications(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MentorApplicationsResponse:
    mentors = PostService(db).get_applications(post_id, current_user)
    return MentorApplicationsResponse(
        post_id=post_id,
        mentors=[MentorApplicationSummary.model_validate(mentor) for mentor in mentors],
    )
