from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.database.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import ErrorResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="데모 로그인",
    description=(
        "샘플 사용자 ID로 로그인하여 JWT 액세스 토큰을 발급합니다. "
        "Swagger 우측 상단 `Authorize` 버튼에서 `Bearer {token}` 형식으로 사용합니다."
    ),
    responses={
        200: {"description": "로그인 성공 및 JWT 발급"},
        404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"},
    },
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)
