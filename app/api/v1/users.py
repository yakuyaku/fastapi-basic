"""
User API endpoints (v1) - Controller Layer
"""
from fastapi import APIRouter, Query, Request, Depends, status
from typing import Optional
from app.schemas.user import (
    UserListResponse,
    UserResponse,
    UserCreate,
    UserCreateResponse,
    UserDeleteResponse,
    UserSoftDeleteResponse,
    UserUpdate,
    UserUpdateResponse
)
from app.services.user_service import UserService
from app.domain.entities.user import UserEntity
from app.api.dependencies import (
    get_user_service,
    get_current_user,
    get_current_admin_user
)


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    사용자 생성 (회원가입) - 공개 API

    인증 불필요 (회원가입용)

    - **email**: 이메일 주소 (unique)
    - **username**: 사용자명 (unique, 3-50자, 영문/숫자/_/- 만 가능)
    - **password**: 비밀번호 (8-100자, 영문+숫자 필수)
    - **is_admin**: 관리자 여부 (기본값: false)
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    user = await user_service.create_user(user_data)

    # Entity를 Response schema로 변환
    return UserCreateResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at
    )


@router.get("/", response_model=UserListResponse)
async def get_users(
    request: Request,
    current_user: UserEntity = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(10, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (username 또는 email)"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    is_admin: Optional[bool] = Query(None, description="관리자 필터"),
    sort_by: str = Query("created_at", description="정렬 기준 (id, username, email, created_at)"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="정렬 순서")
):
    """
    사용자 목록 조회 - 관리자 전용

    **인증 필요**: Bearer Token (관리자)
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    result = await user_service.list_users(
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
        is_admin=is_admin,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Entity 리스트를 Response schema로 변환
    return UserListResponse(
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
        users=[
            UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                is_admin=user.is_admin,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login_at=user.last_login_at
            )
            for user in result["users"]
        ]
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    request: Request,
    user_id: int,
    current_user: UserEntity = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    특정 사용자 조회

    **인증 필요**: Bearer Token
    - 본인 정보는 누구나 조회 가능
    - 타인 정보는 관리자만 조회 가능

    - **user_id**: 사용자 ID
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출 (권한 검증 포함)
    user = await user_service.get_user(user_id, current_user)

    # Entity를 Response schema로 변환
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at
    )


@router.put("/{user_id}", response_model=UserUpdateResponse)
async def update_user(
    request: Request,
    user_id: int,
    user_update: UserUpdate,
    current_user: UserEntity = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    사용자 정보 전체 수정 (PUT)

    **인증 필요**: Bearer Token
    - 본인 정보는 누구나 수정 가능
    - 타인 정보는 관리자만 수정 가능
    - is_admin 변경은 관리자만 가능

    - **user_id**: 수정할 사용자 ID
    - **email**: 새 이메일 (선택)
    - **username**: 새 사용자명 (선택)
    - **password**: 새 비밀번호 (선택)
    - **is_admin**: 관리자 여부 (선택, 관리자만)

    모든 필드가 선택사항이지만, 최소 1개 이상의 필드를 제공해야 합니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출 (권한 검증 및 비즈니스 로직 포함)
    user = await user_service.update_user(user_id, user_update, current_user)

    # Entity를 Response schema로 변환
    return UserUpdateResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        is_admin=user.is_admin,
        updated_at=user.updated_at
    )


@router.patch("/{user_id}", response_model=UserUpdateResponse)
async def partial_update_user(
    request: Request,
    user_id: int,
    user_update: UserUpdate,
    current_user: UserEntity = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    사용자 정보 부분 수정 (PATCH)

    **인증 필요**: Bearer Token
    - 본인 정보는 누구나 수정 가능
    - 타인 정보는 관리자만 수정 가능

    - **user_id**: 수정할 사용자 ID
    - **email**: 새 이메일 (선택)
    - **username**: 새 사용자명 (선택)
    - **password**: 새 비밀번호 (선택)
    - **is_admin**: 관리자 여부 (선택, 관리자만)

    제공된 필드만 수정됩니다.
    """
    # PUT과 동일한 로직 사용 (Pydantic의 exclude_unset 덕분에)
    return await update_user(request, user_id, user_update, current_user, user_service)


@router.delete("/{user_id}", response_model=UserDeleteResponse)
async def delete_user(
    request: Request,
    user_id: int,
    current_user: UserEntity = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    사용자 삭제 (Hard Delete) - 관리자 전용

    **인증 필요**: Bearer Token (관리자)

    - **user_id**: 삭제할 사용자 ID

    주의: 실제 삭제되며 복구할 수 없습니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출 (비즈니스 로직 포함)
    user = await user_service.delete_user(user_id, current_user)

    # Entity를 Response schema로 변환
    return UserDeleteResponse(
        id=user.id,
        username=user.username,
        email=user.email
    )


@router.patch("/{user_id}/deactivate", response_model=UserSoftDeleteResponse)
async def deactivate_user(
    request: Request,
    user_id: int,
    current_user: UserEntity = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    사용자 비활성화 (Soft Delete) - 관리자 전용

    **인증 필요**: Bearer Token (관리자)

    - **user_id**: 비활성화할 사용자 ID

    사용자를 비활성화하며, 복구 가능합니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출 (비즈니스 로직 포함)
    user = await user_service.soft_delete_user(user_id, current_user)

    # Entity를 Response schema로 변환
    return UserSoftDeleteResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active
    )


@router.patch("/{user_id}/restore")
async def restore_user(
    request: Request,
    user_id: int,
    current_user: UserEntity = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    사용자 복구 (Soft Delete 취소) - 관리자 전용

    **인증 필요**: Bearer Token (관리자)

    - **user_id**: 복구할 사용자 ID
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출 (비즈니스 로직 포함)
    user = await user_service.restore_user(user_id)

    # Entity를 dict로 변환하여 반환
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "message": "사용자가 복구되었습니다"
    }
