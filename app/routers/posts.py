from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models import User
from app.schemas.common import ErrorResponse
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


@router.post(
    "",
    response_model=MentoringPostDetail,
    status_code=status.HTTP_201_CREATED,
    summary="멘토링 게시글 생성",
    description="로그인한 사용자가 멘토링 요청 게시글을 생성합니다.",
    responses={
        201: {"description": "게시글 생성 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        422: {"description": "제목 또는 전공 누락"},
    },
)
def create_post(
    payload: MentoringPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MentoringPostDetail:
    post = PostService(db).create_post(payload, current_user)
    return MentoringPostDetail.model_validate(post)


@router.get(
    "",
    response_model=list[MentoringPostListItem],
    summary="멘토링 게시글 목록 조회",
    description="로그인한 사용자가 전체 멘토링 게시글 목록을 조회합니다.",
    responses={
        200: {"description": "게시글 목록 조회 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
    },
)
def list_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MentoringPostListItem]:
    del current_user
    posts = PostService(db).list_posts()
    return [MentoringPostListItem.model_validate(post) for post in posts]


@router.get(
    "/{post_id}",
    response_model=MentoringPostDetail,
    summary="멘토링 게시글 상세 조회",
    description="게시글 제목, 설명, 원하는 전공, 작성자 정보를 조회합니다.",
    responses={
        200: {"description": "게시글 상세 조회 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        404: {"model": ErrorResponse, "description": "게시글을 찾을 수 없음"},
    },
)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MentoringPostDetail:
    del current_user
    post = PostService(db).get_post(post_id)
    return MentoringPostDetail.model_validate(post)


@router.patch(
    "/{post_id}",
    response_model=MentoringPostDetail,
    summary="멘토링 게시글 수정",
    description="게시글 작성자만 제목, 설명, 전공을 수정할 수 있습니다.",
    responses={
        200: {"description": "게시글 수정 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "작성자 권한 없음"},
        404: {"model": ErrorResponse, "description": "게시글을 찾을 수 없음"},
        422: {"description": "제목 또는 전공 누락"},
    },
)
def update_post(
    post_id: int,
    payload: MentoringPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MentoringPostDetail:
    post = PostService(db).update_post(post_id, payload, current_user)
    return MentoringPostDetail.model_validate(post)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="멘토링 게시글 삭제",
    description="게시글 작성자만 해당 게시글을 삭제할 수 있습니다.",
    responses={
        204: {"description": "게시글 삭제 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "작성자 권한 없음"},
        404: {"model": ErrorResponse, "description": "게시글을 찾을 수 없음"},
    },
)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    PostService(db).delete_post(post_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{post_id}/applications",
    response_model=MentorApplicationsResponse,
    summary="멘토 지원자 목록 조회",
    description="게시글 작성자가 해당 게시글에 지원한 멘토 목록을 조회합니다.",
    responses={
        200: {"description": "멘토 지원자 목록 조회 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "작성자 권한 없음"},
        404: {"model": ErrorResponse, "description": "게시글을 찾을 수 없음"},
    },
)
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
