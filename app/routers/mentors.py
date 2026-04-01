from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models import User
from app.schemas.common import ErrorResponse
from app.schemas.user import MentorDetailResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/mentors", tags=["mentors"])


@router.get(
    "/{mentor_id}",
    response_model=MentorDetailResponse,
    summary="멘토 상세 조회",
    description="멘토 상세 정보와 전체 지원 횟수를 조회합니다.",
    responses={
        200: {"description": "멘토 상세 조회 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        404: {"model": ErrorResponse, "description": "멘토를 찾을 수 없음"},
    },
)
def get_mentor_detail(
    mentor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MentorDetailResponse:
    del current_user
    return UserService(db).get_mentor_detail(mentor_id)
