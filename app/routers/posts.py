from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models import PostRole, User
from app.schemas.common import ErrorResponse
from app.schemas.post import (
    MentorApplicationsResponse,
    MentoringPostCreate,
    MentoringPostDetail,
    MentoringPostListItem,
    MentoringPostUpdate,
    MentorSelectRequest,
    MentorSelectResponse,
    ReviewCreateRequest,
    ReviewResponse,
)
from app.schemas.user import MentorApplicationSummary
from app.services.dto import (
    PostApplyDTO,
    PostCreateDTO,
    PostListQueryDTO,
    PostOwnershipDTO,
    PostReviewUpsertDTO,
    PostSelectMentorDTO,
    PostUpdateDTO,
)
from app.services.post_api_services import (
    ApplyToPostService,
    CreatePostService,
    DeletePostService,
    GetPostApplicationsService,
    GetPostService,
    GetSelectedMentorService,
    ListPostsService,
    SelectMentorService,
    UpdatePostService,
    UpsertPostReviewService,
)

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post(
    "",
    response_model=MentoringPostDetail,
    status_code=status.HTTP_201_CREATED,
    summary="멘토링 게시글 생성",
    description="로그인한 사용자가 role(MENTEE/MENTOR)을 지정하여 멘토링 게시글을 생성합니다.",
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
    command = PostCreateDTO(
        author_id=current_user.id,
        title=payload.title,
        image_url=payload.image_url,
        description=payload.description,
        major=payload.major,
        role=payload.role,
    )
    post = CreatePostService(db).execute(command)
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
    keyword: str | None = Query(default=None, description="제목/설명/전공 통합 검색어"),
    major: str | None = Query(default=None, description="전공 정확 일치 필터"),
    role: PostRole | None = Query(default=None, description="게시글 역할 필터(MENTEE/MENTOR)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MentoringPostListItem]:
    del current_user
    posts = ListPostsService(db).execute(
        PostListQueryDTO(keyword=keyword, major=major, role=role)
    )
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
    post = GetPostService(db).execute(post_id)
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
    command = PostUpdateDTO(
        post_id=post_id,
        user_id=current_user.id,
        title=payload.title,
        image_url=payload.image_url,
        description=payload.description,
        major=payload.major,
    )
    post = UpdatePostService(db).execute(command)
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
    DeletePostService(db).execute(PostOwnershipDTO(post_id=post_id, user_id=current_user.id))
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
    mentors = GetPostApplicationsService(db).execute(
        PostOwnershipDTO(post_id=post_id, user_id=current_user.id)
    )
    return MentorApplicationsResponse(
        post_id=post_id,
        mentors=[MentorApplicationSummary.model_validate(mentor) for mentor in mentors],
    )


@router.post(
    "/{post_id}/apply",
    status_code=status.HTTP_201_CREATED,
    summary="게시글 지원",
    description=(
        "로그인한 사용자가 게시글에 지원합니다. "
        "(MENTEE 글에는 멘토, MENTOR 글에는 멘티가 지원)"
    ),
    responses={
        201: {"description": "게시글 지원 성공"},
        400: {"model": ErrorResponse, "description": "중복 지원 또는 본인 게시글 지원"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        404: {"model": ErrorResponse, "description": "게시글을 찾을 수 없음"},
    },
)
def apply_to_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    ApplyToPostService(db).execute(
        PostApplyDTO(post_id=post_id, applicant_id=current_user.id)
    )
    return {"message": "멘토 지원이 완료되었습니다"}


@router.post(
    "/{post_id}/select-mentor",
    response_model=MentorSelectResponse,
    summary="지원자 확정",
    description="게시글 작성자가 지원자 중 한 명을 최종 확정합니다.",
    responses={
        200: {"description": "멘토 확정 성공"},
        400: {"model": ErrorResponse, "description": "지원하지 않은 멘토 선택"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "작성자 권한 없음"},
        404: {"model": ErrorResponse, "description": "게시글 또는 멘토를 찾을 수 없음"},
    },
)
def select_mentor(
    post_id: int,
    payload: MentorSelectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MentorSelectResponse:
    command = PostSelectMentorDTO(
        post_id=post_id,
        selector_id=current_user.id,
        mentor_id=payload.mentor_id,
    )
    match = SelectMentorService(db).execute(command)
    return MentorSelectResponse(
        post_id=post_id,
        mentor=MentorApplicationSummary.model_validate(match.mentor),
        selected_at=match.selected_at,
    )


@router.get(
    "/{post_id}/selected-mentor",
    response_model=MentorSelectResponse,
    summary="확정 지원자 조회",
    description="게시글 작성자가 최종 확정한 지원자를 조회합니다.",
    responses={
        200: {"description": "확정 멘토 조회 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "작성자 권한 없음"},
        404: {"model": ErrorResponse, "description": "확정 멘토 없음 또는 게시글 없음"},
    },
)
def get_selected_mentor(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MentorSelectResponse:
    match = GetSelectedMentorService(db).execute(
        PostOwnershipDTO(post_id=post_id, user_id=current_user.id)
    )
    return MentorSelectResponse(
        post_id=post_id,
        mentor=MentorApplicationSummary.model_validate(match.mentor),
        selected_at=match.selected_at,
    )


@router.post(
    "/{post_id}/review",
    response_model=ReviewResponse,
    summary="멘토 별점 등록",
    description=(
        "게시글 role 기준으로 멘티 역할 사용자만 "
        "확정된 멘토에게 별점/리뷰를 남길 수 있습니다."
    ),
    responses={
        200: {"description": "별점 등록 성공"},
        400: {"model": ErrorResponse, "description": "멘토 확정 전 리뷰 등록 시도"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "멘티 역할 사용자 아님"},
        404: {"model": ErrorResponse, "description": "게시글을 찾을 수 없음"},
    },
)
def create_review(
    post_id: int,
    payload: ReviewCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewResponse:
    review = UpsertPostReviewService(db).execute(
        PostReviewUpsertDTO(
            post_id=post_id,
            reviewer_id=current_user.id,
            rating=payload.rating,
            comment=payload.comment,
        )
    )
    return ReviewResponse(
        post_id=post_id,
        mentor_id=review.mentor_id,
        mentee_id=review.mentee_id,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
    )
