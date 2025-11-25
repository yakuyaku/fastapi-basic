"""
Auth API endpoints (v1) - Controller Layer
"""
from fastapi import APIRouter, HTTPException, status, Request, Depends
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import AuthService
from app.domain.entities.user import UserEntity
from app.api.dependencies import get_auth_service, get_current_user
from app.core.config import settings
from app.core.security import decode_access_token
from app.core.logging import logger


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/dev-token")
async def get_dev_token(request: Request):
    """
    개발 전용 고정 토큰 반환

    ⚠️ 개발 환경에서만 사용 가능
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # 운영 환경에서는 비활성화
    if not settings.is_development:
        logger.warning(f"[{request_id}] 운영 환경에서 개발 토큰 요청 시도")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 기능은 개발 환경에서만 사용 가능합니다"
        )

    # 개발 토큰이 설정되지 않은 경우
    if not settings.DEV_ACCESS_TOKEN:
        logger.warning(f"[{request_id}] 개발 토큰이 설정되지 않음")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="개발 토큰이 설정되지 않았습니다. .env 파일을 확인하세요."
        )

    # 토큰 디코딩하여 사용자 정보 추출
    payload = decode_access_token(settings.DEV_ACCESS_TOKEN)

    if not payload:
        logger.error(f"[{request_id}] 개발 토큰이 유효하지 않음")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="개발 토큰이 유효하지 않습니다. 다시 생성하세요."
        )

    logger.info(f"[{request_id}] 개발 토큰 반환 - user_id: {payload.get('user_id')}")

    return LoginResponse(
        access_token=settings.DEV_ACCESS_TOKEN,
        token_type="bearer",
        user={
            "id": payload.get("user_id"),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "is_admin": True  # 개발 사용자는 관리자로 가정
        }
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    로그인

    - **email**: 이메일 주소
    - **password**: 비밀번호

    성공 시 JWT Access Token을 반환합니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출 (비즈니스 로직 포함)
    token, user = await auth_service.login(login_data)

    # Response 반환
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_admin": user.is_admin
        }
    )


@router.get("/me")
async def get_me(
    request: Request,
    current_user: UserEntity = Depends(get_current_user)
):
    """
    현재 로그인한 사용자 정보 조회

    JWT 토큰이 필요합니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    logger.info(f"[{request_id}] 현재 사용자 조회 - ID: {current_user.id}")

    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at
    }


@router.post("/logout")
async def logout(
    request: Request,
    current_user: UserEntity = Depends(get_current_user)
):
    """
    로그아웃

    클라이언트에서 토큰을 삭제하도록 안내합니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    logger.info(f"[{request_id}] 로그아웃 - ID: {current_user.id}")

    return {
        "message": "로그아웃되었습니다. 클라이언트에서 토큰을 삭제해주세요."
    }
