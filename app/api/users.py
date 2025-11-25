"""
User API 엔드포인트
app/api/users.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime
import math

from app.schemas.user import (
    UserResponse,
    UserListResponse,
    UserCreate,
    UserUpdate
)
from app.core.dependencies import (
    get_current_user,
    get_current_admin_user
)
from app.core.security import get_password_hash, verify_password
from app.db.database import execute_query, fetch_one, fetch_all
from app.core.logging import logger

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
        user: UserCreate,
        current_user: dict = Depends(get_current_admin_user)  # 관리자만
):
    """
    사용자 생성 (관리자 권한 필요)
    """
    # 이메일 중복 확인
    check_query = "SELECT id FROM users WHERE email = %s"
    existing_user = await fetch_one(check_query, (user.email,))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다"
        )

    # 사용자명 중복 확인
    check_query = "SELECT id FROM users WHERE username = %s"
    existing_user = await fetch_one(check_query, (user.username,))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 사용자명입니다"
        )

    # 비밀번호 해싱
    hashed_password = get_password_hash(user.password)

    # 사용자 생성
    insert_query = """
                   INSERT INTO users (username, email, full_name, hashed_password, is_active, is_superuser)
                   VALUES (%s, %s, %s, %s, %s, %s) \
                   """
    user_id = await execute_query(
        insert_query,
        (user.username, user.email, user.full_name, hashed_password, True, False)
    )

    # 생성된 사용자 조회
    select_query = """
                   SELECT id, username, email, full_name, is_active, is_superuser, created_at, updated_at
                   FROM users
                   WHERE id = %s \
                   """
    created_user = await fetch_one(select_query, (user_id,))

    # created_at, updated_at 기본값 처리
    if created_user.get('created_at') is None:
        created_user['created_at'] = datetime.now()
    if created_user.get('updated_at') is None:
        created_user['updated_at'] = datetime.now()

    logger.info(f"사용자 생성 완료 - ID: {user_id}, Username: {user.username}")

    return UserResponse(**created_user)


@router.get("/", response_model=UserListResponse)
async def get_users(
        page: int = Query(1, ge=1, description="페이지 번호"),
        page_size: int = Query(10, ge=1, le=100, description="페이지 크기"),
        search: str = Query(None, description="검색어 (username, email, full_name)"),
        is_active: bool = Query(None, description="활성화 상태 필터"),
        sort_by: str = Query("created_at", description="정렬 기준"),
        sort_order: str = Query("desc", description="정렬 순서 (asc, desc)"),
        current_user: dict = Depends(get_current_user)  # 인증된 사용자만
):
    """
    사용자 목록 조회 (인증 필요)
    """
    # 정렬 순서 검증
    if sort_order.lower() not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="정렬 순서는 'asc' 또는 'desc'만 가능합니다"
        )

    # 정렬 기준 검증
    allowed_sort_fields = ["id", "username", "email", "created_at", "updated_at"]
    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"정렬 기준은 {', '.join(allowed_sort_fields)} 중 하나여야 합니다"
        )

    # 기본 쿼리
    base_query = "FROM users WHERE 1=1"
    params = []

    # 검색 조건
    if search:
        base_query += " AND (username LIKE %s OR email LIKE %s OR full_name LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    # 활성화 상태 필터
    if is_active is not None:
        base_query += " AND is_active = %s"
        params.append(is_active)

    # 전체 개수 조회
    count_query = f"SELECT COUNT(*) as total {base_query}"
    count_result = await fetch_one(count_query, tuple(params))
    total = count_result['total']  # ✅ [0] 제거!

    # 페이지네이션
    offset = (page - 1) * page_size
    total_pages = math.ceil(total / page_size)

    # 사용자 목록 조회
    select_query = f"""
        SELECT id, username, email, full_name, is_active, is_superuser, 
               created_at, updated_at 
        {base_query}
        ORDER BY {sort_by} {sort_order.upper()}
        LIMIT %s OFFSET %s
    """
    params.extend([page_size, offset])
    users_data = await fetch_all(select_query, tuple(params))

    # created_at, updated_at 기본값 처리
    current_time = datetime.now()
    for user in users_data:
        if user.get('created_at') is None:
            user['created_at'] = current_time
        if user.get('updated_at') is None:
            user['updated_at'] = current_time

    users = [UserResponse(**user) for user in users_data]

    logger.info(f"사용자 목록 조회 - 페이지: {page}, 총 {total}명")

    return UserListResponse(
        users=users,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
        user_id: int,
        current_user: dict = Depends(get_current_user)  # 인증된 사용자만
):
    """
    특정 사용자 조회 (인증 필요)
    """
    query = """
            SELECT id, username, email, full_name, is_active, is_superuser, created_at, updated_at
            FROM users
            WHERE id = %s \
            """
    user = await fetch_one(query, (user_id,))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    # created_at, updated_at 기본값 처리
    if user.get('created_at') is None:
        user['created_at'] = datetime.now()
    if user.get('updated_at') is None:
        user['updated_at'] = datetime.now()

    return UserResponse(**user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
        user_id: int,
        user_update: UserUpdate,
        current_user: dict = Depends(get_current_user)  # 인증된 사용자만
):
    """
    사용자 정보 수정 (본인 또는 관리자만 가능)
    """
    # 권한 확인: 본인이거나 관리자여야 함
    is_admin = current_user.get('is_admin', False) or current_user.get('is_superuser', False)
    if current_user["id"] != user_id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인의 정보만 수정할 수 있습니다"
        )

    # 사용자 존재 확인
    check_query = "SELECT id FROM users WHERE id = %s"
    existing_user = await fetch_one(check_query, (user_id,))

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    # 수정할 필드 수집
    update_fields = []
    params = []

    if user_update.username is not None:
        # 사용자명 중복 확인
        check_query = "SELECT id FROM users WHERE username = %s AND id != %s"
        existing = await fetch_one(check_query, (user_update.username, user_id))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 사용자명입니다"
            )
        update_fields.append("username = %s")
        params.append(user_update.username)

    if user_update.email is not None:
        # 이메일 중복 확인
        check_query = "SELECT id FROM users WHERE email = %s AND id != %s"
        existing = await fetch_one(check_query, (user_update.email, user_id))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다"
            )
        update_fields.append("email = %s")
        params.append(user_update.email)

    if user_update.full_name is not None:
        update_fields.append("full_name = %s")
        params.append(user_update.full_name)

    if user_update.password is not None:
        hashed_password = get_password_hash(user_update.password)
        update_fields.append("hashed_password = %s")
        params.append(hashed_password)

    # 관리자만 is_active 수정 가능
    if user_update.is_active is not None and is_admin:
        update_fields.append("is_active = %s")
        params.append(user_update.is_active)

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 내용이 없습니다"
        )

    # 업데이트 실행
    params.append(user_id)
    update_query = f"""
        UPDATE users 
        SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    await execute_query(update_query, tuple(params))

    # 수정된 사용자 조회
    select_query = """
                   SELECT id, username, email, full_name, is_active, is_superuser, created_at, updated_at
                   FROM users
                   WHERE id = %s \
                   """
    updated_user = await fetch_one(select_query, (user_id,))

    # created_at, updated_at 기본값 처리
    if updated_user.get('created_at') is None:
        updated_user['created_at'] = datetime.now()
    if updated_user.get('updated_at') is None:
        updated_user['updated_at'] = datetime.now()

    logger.info(f"사용자 수정 완료 - ID: {user_id}")

    return UserResponse(**updated_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
        user_id: int,
        current_user: dict = Depends(get_current_admin_user)  # 관리자만
):
    """
    사용자 삭제 (관리자 권한 필요)
    """
    # 자기 자신은 삭제 불가
    if current_user["id"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신은 삭제할 수 없습니다"
        )

    # 사용자 존재 확인
    check_query = "SELECT id FROM users WHERE id = %s"
    existing_user = await fetch_one(check_query, (user_id,))

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    # 사용자 삭제
    delete_query = "DELETE FROM users WHERE id = %s"
    await execute_query(delete_query, (user_id,))

    logger.info(f"사용자 삭제 완료 - ID: {user_id}")

    return None