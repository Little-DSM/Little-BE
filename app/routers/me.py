from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models import User
from app.schemas.common import ErrorResponse
from app.schemas.user import MentoringProgressListResponse, MyPageResponse, MyPageUpdateRequest
from app.services.user_service import UserService

router = APIRouter(prefix="/me", tags=["me"])


@router.get(
    "",
    response_model=MyPageResponse,
    summary="내 마이페이지 조회",
    description="로그인한 사용자의 이름, 자기소개, 프로필 이미지, 전공을 조회합니다.",
    responses={
        200: {"description": "마이페이지 조회 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
    },
)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MyPageResponse:
    return UserService(db).get_my_profile(current_user)


@router.patch(
    "",
    response_model=MyPageResponse,
    summary="내 마이페이지 수정",
    description="로그인한 사용자의 이름, 자기소개, 프로필 이미지, 전공을 수정합니다.",
    responses={
        200: {"description": "마이페이지 수정 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        422: {"description": "입력값 검증 실패"},
    },
)
def update_my_profile(
    payload: MyPageUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MyPageResponse:
    return UserService(db).update_my_profile(current_user, payload)


@router.get(
    "/mentoring-progress",
    response_model=MentoringProgressListResponse,
    summary="내 멘토링 진행상황 조회",
    description=(
        "로그인한 멘티가 확정한 멘토링 목록을 조회합니다. "
        "각 항목은 멘토 연락처와 상태(IN_PROGRESS/COMPLETED)를 포함합니다."
    ),
    responses={
        200: {"description": "내 멘토링 진행상황 조회 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
    },
)
def get_my_mentoring_progress(
    status: Literal["all", "in_progress", "completed"] = Query(
        default="all",
        description="상태 필터(all/in_progress/completed)",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MentoringProgressListResponse:
    return UserService(db).get_my_mentoring_progress(current_user, status)
