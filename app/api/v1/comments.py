"""
Comment API endpoints (v1) - Controller Layer
app/api/v1/comments.py
"""
from fastapi import APIRouter, Request, Depends, Query, status
from typing import Optional
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentTreeResponse,
    CommentListResponse,
    CommentTreeListResponse,
    CommentCreateResponse,
    CommentUpdateResponse,
    CommentDeleteResponse
)
from app.services.comment_service import CommentService
from app.domain.entities.user import UserEntity
from app.api.dependencies import (
    get_comment_service,
    get_current_user,
    get_optional_user,
    get_current_admin_user
)


router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/posts/{post_id}", response_model=CommentCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
        request: Request,
        post_id: int,
        comment_data: CommentCreate,
        current_user: Optional[UserEntity] = Depends(get_optional_user),
        comment_service: CommentService = Depends(get_comment_service)
):
    """
    댓글 작성

    **인증**: 선택 (게스트 사용자 허용)

    - **post_id**: 게시글 ID
    - **content**: 댓글 내용 (1-1000자)
    - **parent_id**: 부모 댓글 ID (대댓글인 경우, 선택)

    Tree 구조:
    - 최상위 댓글: parent_id = None, depth = 0
    - 1차 대댓글: parent_id = 상위댓글ID, depth = 1
    - 2차 대댓글: parent_id = 1차댓글ID, depth = 2
    - 최대 깊이: 3 (0, 1, 2, 3)

    인증된 사용자는 본인 이름으로, 게스트는 "guest"로 등록됩니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    comment, generated_password = await comment_service.create_comment(post_id, comment_data, current_user)

    # Entity를 Response schema로 변환
    return CommentCreateResponse(
        id=comment.id,
        post_id=comment.post_id,
        parent_id=comment.parent_id,
        content=comment.content,
        depth=comment.depth,
        path=comment.path,
        author_id=comment.author_id,
        created_at=comment.created_at,
        generated_password=generated_password
    )


@router.get("/posts/{post_id}/flat", response_model=CommentListResponse)
async def get_post_comments_flat(
        request: Request,
        post_id: int,
        comment_service: CommentService = Depends(get_comment_service),
        include_deleted: bool = Query(False, description="삭제된 댓글 포함 (관리자 전용)")
):
    """
    게시글의 댓글 목록 조회 (Flat 구조)

    **인증**: 불필요

    - **post_id**: 게시글 ID
    - **include_deleted**: 삭제된 댓글 포함 여부 (기본값: false)

    Returns:
        Flat 구조의 댓글 리스트 (path 순서로 정렬)
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출 (as_tree=False)
    comments = await comment_service.get_post_comments(
        post_id,
        include_deleted=include_deleted,
        as_tree=False
    )

    # 전체 개수
    total = await comment_service.get_comment_count(post_id)

    # Entity를 Response schema로 변환
    return CommentListResponse(
        post_id=post_id,
        total=total,
        comments=[
            CommentResponse(
                id=comment.id,
                post_id=comment.post_id,
                parent_id=comment.parent_id,
                author_id=comment.author_id,
                content=comment.content,
                depth=comment.depth,
                path=comment.path,
                order_num=comment.order_num,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
                is_deleted=comment.is_deleted,
                author_username=comment.author_username,
                author_email=comment.author_email
            )
            for comment in comments
        ]
    )


@router.get("/posts/{post_id}/tree", response_model=CommentTreeListResponse)
async def get_post_comments_tree(
        request: Request,
        post_id: int,
        comment_service: CommentService = Depends(get_comment_service),
        include_deleted: bool = Query(False, description="삭제된 댓글 포함 (관리자 전용)")
):
    """
    게시글의 댓글 목록 조회 (Tree 구조)

    **인증**: 불필요

    - **post_id**: 게시글 ID
    - **include_deleted**: 삭제된 댓글 포함 여부 (기본값: false)

    Returns:
        Tree 구조의 댓글 리스트 (children에 자식 댓글 포함)
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출 (as_tree=True)
    comments = await comment_service.get_post_comments(
        post_id,
        include_deleted=include_deleted,
        as_tree=True
    )

    # 전체 개수
    total = await comment_service.get_comment_count(post_id)

    # Entity를 Response schema로 재귀 변환
    def to_tree_response(comment):
        return CommentTreeResponse(
            id=comment.id,
            post_id=comment.post_id,
            parent_id=comment.parent_id,
            author_id=comment.author_id,
            content=comment.content,
            depth=comment.depth,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            is_deleted=comment.is_deleted,
            author_username=comment.author_username,
            children=[to_tree_response(child) for child in comment.children]
        )

    return CommentTreeListResponse(
        post_id=post_id,
        total=total,
        comments=[to_tree_response(comment) for comment in comments]
    )


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
        request: Request,
        comment_id: int,
        comment_service: CommentService = Depends(get_comment_service)
):
    """
    특정 댓글 조회

    **인증**: 불필요

    - **comment_id**: 댓글 ID

    Returns:
        댓글 상세 정보
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    comment = await comment_service.get_comment(comment_id)

    # Entity를 Response schema로 변환
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        parent_id=comment.parent_id,
        author_id=comment.author_id,
        content=comment.content,
        depth=comment.depth,
        path=comment.path,
        order_num=comment.order_num,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        is_deleted=comment.is_deleted,
        author_username=comment.author_username,
        author_email=comment.author_email
    )


@router.put("/{comment_id}", response_model=CommentUpdateResponse)
async def update_comment(
        request: Request,
        comment_id: int,
        comment_data: CommentUpdate,
        current_user: Optional[UserEntity] = Depends(get_optional_user),
        comment_service: CommentService = Depends(get_comment_service)
):
    """
    댓글 수정

    **인증**: 선택 (게스트 댓글은 비밀번호 필요)
    - 본인이 작성한 댓글만 수정 가능
    - 관리자는 모든 댓글 수정 가능
    - **게스트 댓글 수정 시 password 필드 필수**

    - **comment_id**: 댓글 ID
    - **content**: 새 댓글 내용
    - **password**: 게스트 댓글 비밀번호 (게스트 댓글 수정 시 필수)
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    comment = await comment_service.update_comment(comment_id, comment_data, current_user)

    # Entity를 Response schema로 변환
    return CommentUpdateResponse(
        id=comment.id,
        content=comment.content,
        updated_at=comment.updated_at
    )


@router.patch("/{comment_id}", response_model=CommentUpdateResponse)
async def partial_update_comment(
        request: Request,
        comment_id: int,
        comment_data: CommentUpdate,
        current_user: Optional[UserEntity] = Depends(get_optional_user),
        comment_service: CommentService = Depends(get_comment_service)
):
    """
    댓글 부분 수정 (PATCH)

    **인증**: 선택 (게스트 댓글은 비밀번호 필요)

    PUT과 동일한 동작 (댓글은 content만 수정 가능)
    """
    return await update_comment(request, comment_id, comment_data, current_user, comment_service)


@router.delete("/{comment_id}", response_model=CommentDeleteResponse)
async def delete_comment(
        request: Request,
        comment_id: int,
        current_user: Optional[UserEntity] = Depends(get_optional_user),
        comment_service: CommentService = Depends(get_comment_service),
        hard_delete: bool = Query(False, description="Hard Delete 여부 (관리자 전용)"),
        password: Optional[str] = Query(None, description="게스트 댓글 비밀번호")
):
    """
    댓글 삭제

    **인증**: 선택 (게스트 댓글은 비밀번호 필요)
    - 본인이 작성한 댓글만 삭제 가능
    - 관리자는 모든 댓글 삭제 가능
    - **게스트 댓글 삭제 시 password 쿼리 파라미터 필수**

    - **comment_id**: 댓글 ID
    - **password**: 게스트 댓글 비밀번호 (게스트 댓글 삭제 시 필수)
    - **hard_delete**: Hard Delete 여부 (기본값: false, 관리자 전용)

    Soft Delete (기본):
    - content를 "삭제된 댓글입니다"로 변경
    - is_deleted = 1

    Hard Delete (관리자):
    - 실제 삭제 (CASCADE로 자식 댓글도 삭제됨)
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    comment = await comment_service.delete_comment(comment_id, current_user, hard_delete, password)

    # Entity를 Response schema로 변환
    return CommentDeleteResponse(
        id=comment.id
    )


@router.patch("/{comment_id}/restore", response_model=CommentResponse)
async def restore_comment(
        request: Request,
        comment_id: int,
        current_user: UserEntity = Depends(get_current_admin_user),
        comment_service: CommentService = Depends(get_comment_service)
):
    """
    삭제된 댓글 복구 - 관리자 전용

    **인증 필요**: Bearer Token (관리자)

    - **comment_id**: 댓글 ID

    주의: 내용은 "삭제된 댓글입니다"로 남아있습니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    comment = await comment_service.restore_comment(comment_id)

    # Entity를 Response schema로 변환
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        parent_id=comment.parent_id,
        author_id=comment.author_id,
        content=comment.content,
        depth=comment.depth,
        path=comment.path,
        order_num=comment.order_num,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        is_deleted=comment.is_deleted,
        author_username=comment.author_username,
        author_email=comment.author_email
    )