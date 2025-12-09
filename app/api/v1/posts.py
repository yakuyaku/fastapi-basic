"""
Post API endpoints (v1) - Controller Layer
app/api/v1/posts.py
"""
from fastapi import APIRouter, Query, Request, Depends, status
from typing import Optional
from app.schemas.post import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostListResponse,
    PostCreateResponse,
    PostUpdateResponse,
    PostDeleteResponse,
    PostRestoreResponse,
    PostTogglePinResponse,
    PostToggleLockResponse,
    PostLikeResponse
)
from app.services.post_service import PostService
from app.domain.entities.user import UserEntity
from app.api.dependencies import (
    get_post_service,
    get_current_user,
    get_optional_user,
    get_current_admin_user
)


router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=PostCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
        request: Request,
        post_data: PostCreate,
        current_user: Optional[UserEntity] = Depends(get_optional_user),
        post_service: PostService = Depends(get_post_service)
):
    """
    게시글 작성

    **인증**: 선택 (게스트 사용자 허용)

    - **title**: 게시글 제목 (1-200자)
    - **content**: 게시글 내용 (필수)
    - **is_pinned**: 고정 게시글 여부 (관리자 전용, 기본값: false)

    인증된 사용자는 본인 이름으로, 게스트는 "guest"로 등록됩니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    post, generated_password = await post_service.create_post(post_data, current_user)

    # Entity를 Response schema로 변환
    return PostCreateResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        author_id=post.author_id,
        view_count=post.view_count,
        like_count=post.like_count,
        created_at=post.created_at,
        is_pinned=post.is_pinned,
        generated_password=generated_password
    )


@router.get("/", response_model=PostListResponse)
async def get_posts(
        request: Request,
        post_service: PostService = Depends(get_post_service),
        current_user: Optional[UserEntity] = Depends(get_optional_user),
        page: int = Query(1, ge=1, description="페이지 번호"),
        page_size: int = Query(10, ge=1, le=100, description="페이지당 항목 수"),
        search: Optional[str] = Query(None, description="검색어 (제목 또는 내용)"),
        author_id: Optional[int] = Query(None, description="작성자 ID 필터"),
        is_pinned: Optional[bool] = Query(None, description="고정 게시글 필터"),
        include_deleted: bool = Query(False, description="삭제된 게시글 포함 (관리자 전용)"),
        sort_by: str = Query("created_at", description="정렬 기준 (id, title, created_at, view_count, like_count)"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="정렬 순서")
):
    """
    게시글 목록 조회

    **인증**: 선택 (로그인 없이도 조회 가능, 삭제된 게시글 조회는 관리자 필요)

    - 고정 게시글이 항상 상단에 표시됩니다
    - 삭제된 게시글은 기본적으로 제외됩니다
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    result = await post_service.list_posts(
        page=page,
        page_size=page_size,
        search=search,
        author_id=author_id,
        is_pinned=is_pinned,
        include_deleted=include_deleted,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user=current_user
    )

    # Entity 리스트를 Response schema로 변환
    return PostListResponse(
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
        posts=[
            PostResponse(
                id=post.id,
                title=post.title,
                content=post.content,
                author_id=post.author_id,
                view_count=post.view_count,
                like_count=post.like_count,
                created_at=post.created_at,
                updated_at=post.updated_at,
                is_deleted=post.is_deleted,
                is_pinned=post.is_pinned,
                is_locked=post.is_locked,
                author_username=post.author_username,
                author_email=post.author_email
            )
            for post in result["posts"]
        ]
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
        request: Request,
        post_id: int,
        current_user: Optional[UserEntity] = Depends(get_optional_user),
        post_service: PostService = Depends(get_post_service),
        increment_view: bool = Query(True, description="조회수 증가 여부")
):
    """
    특정 게시글 조회 (작성자 정보 포함)

    **인증**: 선택 (삭제된 게시글 조회는 관리자 필요)

    - **post_id**: 게시글 ID
    - **increment_view**: 조회수 증가 여부 (기본값: true)

    조회수가 자동으로 증가합니다 (선택 가능)
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    post = await post_service.get_post(post_id, current_user, increment_view)

    # Entity를 Response schema로 변환
    return PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        author_id=post.author_id,
        view_count=post.view_count,
        like_count=post.like_count,
        created_at=post.created_at,
        updated_at=post.updated_at,
        is_deleted=post.is_deleted,
        is_pinned=post.is_pinned,
        is_locked=post.is_locked,
        author_username=post.author_username,
        author_email=post.author_email
    )


@router.put("/{post_id}", response_model=PostUpdateResponse)
async def update_post(
        request: Request,
        post_id: int,
        post_data: PostUpdate,
        current_user: Optional[UserEntity] = Depends(get_optional_user),
        post_service: PostService = Depends(get_post_service)
):
    """
    게시글 전체 수정 (PUT)

    **인증**: 선택 (게스트 게시글은 비밀번호 필요)
    - 본인이 작성한 게시글만 수정 가능
    - 관리자는 모든 게시글 수정 가능
    - 잠긴 게시글은 관리자만 수정 가능
    - 고정/잠금 설정은 관리자만 변경 가능
    - **게스트 게시글 수정 시 password 필드 필수**

    - **post_id**: 수정할 게시글 ID
    - **title**: 새 제목 (선택)
    - **content**: 새 내용 (선택)
    - **password**: 게스트 게시글 비밀번호 (게스트 게시글 수정 시 필수)
    - **is_pinned**: 고정 여부 (선택, 관리자 전용)
    - **is_locked**: 잠금 여부 (선택, 관리자 전용)
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    post = await post_service.update_post(post_id, post_data, current_user)

    # Entity를 Response schema로 변환
    return PostUpdateResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        author_id=post.author_id,
        view_count=post.view_count,
        like_count=post.like_count,
        updated_at=post.updated_at,
        is_pinned=post.is_pinned,
        is_locked=post.is_locked
    )


@router.patch("/{post_id}", response_model=PostUpdateResponse)
async def partial_update_post(
        request: Request,
        post_id: int,
        post_data: PostUpdate,
        current_user: UserEntity = Depends(get_current_user),
        post_service: PostService = Depends(get_post_service)
):
    """
    게시글 부분 수정 (PATCH)

    **인증 필요**: Bearer Token
    - 본인이 작성한 게시글만 수정 가능
    - 관리자는 모든 게시글 수정 가능

    제공된 필드만 수정됩니다.
    """
    # PUT과 동일한 로직 사용 (Pydantic의 exclude_unset 덕분에)
    return await update_post(request, post_id, post_data, current_user, post_service)


@router.delete("/{post_id}", response_model=PostDeleteResponse)
async def delete_post(
        request: Request,
        post_id: int,
        current_user: Optional[UserEntity] = Depends(get_optional_user),
        post_service: PostService = Depends(get_post_service),
        hard_delete: bool = Query(False, description="Hard Delete 여부 (관리자 전용)"),
        password: Optional[str] = Query(None, description="게스트 게시글 비밀번호")
):
    """
    게시글 삭제

    **인증**: 선택 (게스트 게시글은 비밀번호 필요)
    - 본인이 작성한 게시글만 삭제 가능
    - 관리자는 모든 게시글 삭제 가능
    - **게스트 게시글 삭제 시 password 쿼리 파라미터 필수**

    - **post_id**: 삭제할 게시글 ID
    - **password**: 게스트 게시글 비밀번호 (게스트 게시글 삭제 시 필수)
    - **hard_delete**: Hard Delete 여부 (기본값: false, 관리자 전용)

    기본적으로 Soft Delete(is_deleted=1)되며, hard_delete=true인 경우 완전 삭제됩니다 (관리자 전용).
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    post = await post_service.delete_post(post_id, current_user, hard_delete, password)

    # Entity를 Response schema로 변환
    return PostDeleteResponse(
        id=post.id,
        title=post.title
    )


@router.patch("/{post_id}/restore", response_model=PostRestoreResponse)
async def restore_post(
        request: Request,
        post_id: int,
        current_user: UserEntity = Depends(get_current_admin_user),
        post_service: PostService = Depends(get_post_service)
):
    """
    삭제된 게시글 복구 - 관리자 전용

    **인증 필요**: Bearer Token (관리자)

    - **post_id**: 복구할 게시글 ID
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    post = await post_service.restore_post(post_id)

    # Entity를 Response schema로 변환
    return PostRestoreResponse(
        id=post.id,
        title=post.title
    )


@router.patch("/{post_id}/pin", response_model=PostTogglePinResponse)
async def toggle_pin(
        request: Request,
        post_id: int,
        current_user: UserEntity = Depends(get_current_admin_user),
        post_service: PostService = Depends(get_post_service)
):
    """
    게시글 고정/고정 해제 - 관리자 전용

    **인증 필요**: Bearer Token (관리자)

    - **post_id**: 게시글 ID

    고정 상태를 토글합니다 (고정 ↔ 해제)
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    post = await post_service.toggle_pin(post_id, current_user)

    # Entity를 Response schema로 변환
    return PostTogglePinResponse(
        id=post.id,
        title=post.title,
        is_pinned=post.is_pinned
    )


@router.patch("/{post_id}/lock", response_model=PostToggleLockResponse)
async def toggle_lock(
        request: Request,
        post_id: int,
        current_user: UserEntity = Depends(get_current_admin_user),
        post_service: PostService = Depends(get_post_service)
):
    """
    게시글 잠금/잠금 해제 - 관리자 전용

    **인증 필요**: Bearer Token (관리자)

    - **post_id**: 게시글 ID

    잠금 상태를 토글합니다 (잠금 ↔ 해제)
    잠긴 게시글은 관리자만 수정할 수 있습니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    post = await post_service.toggle_lock(post_id, current_user)

    # Entity를 Response schema로 변환
    return PostToggleLockResponse(
        id=post.id,
        title=post.title,
        is_locked=post.is_locked
    )


@router.post("/{post_id}/like", response_model=PostLikeResponse)
async def like_post(
        request: Request,
        post_id: int,
        post_service: PostService = Depends(get_post_service)
):
    """
    게시글 좋아요

    **인증**: 불필요 (누구나 가능)

    - **post_id**: 게시글 ID

    좋아요 수가 1 증가합니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    post = await post_service.increment_like(post_id)

    # Entity를 Response schema로 변환
    return PostLikeResponse(
        id=post.id,
        like_count=post.like_count
    )


@router.delete("/{post_id}/like", response_model=PostLikeResponse)
async def unlike_post(
        request: Request,
        post_id: int,
        post_service: PostService = Depends(get_post_service)
):
    """
    게시글 좋아요 취소

    **인증**: 불필요 (누구나 가능)

    - **post_id**: 게시글 ID

    좋아요 수가 1 감소합니다 (최소 0).
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    post = await post_service.decrement_like(post_id)

    # Entity를 Response schema로 변환
    return PostLikeResponse(
        id=post.id,
        like_count=post.like_count,
        message="좋아요가 취소되었습니다"
    )