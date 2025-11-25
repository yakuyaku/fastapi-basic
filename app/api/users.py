from fastapi import APIRouter, Query, Request, HTTPException, status
from typing import Optional
from app.schemas.user import (
    UserListResponse,
    UserResponse,
    UserCreate,  # 추가
    UserCreateResponse,  # 추가
    UserDeleteResponse,
    UserSoftDeleteResponse,  # 추가
    UserUpdate,  # 추가
    UserUpdateResponse  # 추가
)
from app.core.security import hash_password  # 이미 import 되어 있어야 함
from app.db.database import execute_query, execute_update, get_db_connection, fetch_one, fetch_all
from app.core.security import hash_password  # 추가
from app.core.logging import logger
import math
import aiomysql


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(request: Request, user: UserCreate):
    """
    사용자 생성 (회원가입)

    - **email**: 이메일 주소 (unique)
    - **username**: 사용자명 (unique, 3-50자, 영문/숫자/_/- 만 가능)
    - **password**: 비밀번호 (8-100자, 영문+숫자 필수)
    - **is_admin**: 관리자 여부 (기본값: false)
    """
    request_id = getattr(request.state, "request_id", "no-id")

    logger.info(f"[{request_id}] 사용자 생성 요청 - username: {user.username}, email: {user.email}")

    conn = await get_db_connection()

    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 1. 이메일 중복 체크
            check_email_query = "SELECT id FROM users WHERE email = %s"
            await cursor.execute(check_email_query, (user.email,))
            if await cursor.fetchone():
                logger.warning(f"[{request_id}] 이메일 중복: {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 사용 중인 이메일입니다"
                )

            # 2. 사용자명 중복 체크
            check_username_query = "SELECT id FROM users WHERE username = %s"
            await cursor.execute(check_username_query, (user.username,))
            if await cursor.fetchone():
                logger.warning(f"[{request_id}] 사용자명 중복: {user.username}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 사용 중인 사용자명입니다"
                )

            # 3. 비밀번호 해싱
            hashed_password = hash_password(user.password)

            # 4. 사용자 생성
            insert_query = """
                           INSERT INTO users (email, username, password_hash, is_admin, is_active)
                           VALUES (%s, %s, %s, %s, %s) \
                           """
            await cursor.execute(
                insert_query,
                (user.email, user.username, hashed_password, user.is_admin, True)
            )
            await conn.commit()

            # 5. 생성된 사용자 ID 가져오기
            user_id = cursor.lastrowid

            # 6. 생성된 사용자 정보 조회
            select_query = """
                           SELECT id, email, username, is_active, is_admin, created_at
                           FROM users
                           WHERE id = %s \
                           """
            await cursor.execute(select_query, (user_id,))
            created_user = await cursor.fetchone()

            logger.info(f"[{request_id}] 사용자 생성 완료 - ID: {user_id}, username: {user.username}")

            return UserCreateResponse(**created_user)

    except HTTPException:
        raise
    except Exception as e:
        await conn.rollback()
        logger.error(f"[{request_id}] 사용자 생성 실패: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 생성 중 오류가 발생했습니다"
        )
    finally:
        conn.close()


@router.get("/", response_model=UserListResponse)
async def get_users(
        request: Request,
        page: int = Query(1, ge=1, description="페이지 번호"),
        page_size: int = Query(10, ge=1, le=100, description="페이지당 항목 수"),
        search: Optional[str] = Query(None, description="검색어 (username 또는 email)"),
        is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
        is_admin: Optional[bool] = Query(None, description="관리자 필터"),
        sort_by: str = Query("created_at", description="정렬 기준 (id, username, email, created_at)"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="정렬 순서")
):
    """사용자 목록 조회"""
    request_id = getattr(request.state, "request_id", "no-id")

    # WHERE 조건 구성
    where_conditions = []
    params = []

    if search:
        where_conditions.append("(username LIKE %s OR email LIKE %s)")
        search_term = f"%{search}%"
        params.extend([search_term, search_term])

    if is_active is not None:
        where_conditions.append("is_active = %s")
        params.append(1 if is_active else 0)

    if is_admin is not None:
        where_conditions.append("is_admin = %s")
        params.append(1 if is_admin else 0)

    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

    # 허용된 정렬 컬럼
    allowed_sort_columns = ['id', 'username', 'email', 'created_at']
    if sort_by not in allowed_sort_columns:
        sort_by = 'created_at'

    # 총 개수 조회
    count_query = f"SELECT COUNT(*) as total FROM users WHERE {where_clause}"
    count_result = await fetch_one(count_query, tuple(params))
    total = count_result['total']  # ✅ [0] 제거!

# 페이징 계산
    offset = (page - 1) * page_size
    total_pages = math.ceil(total / page_size)

    # 사용자 목록 조회
    query = f"""
    SELECT 
        id, 
        email, 
        username, 
        is_active, 
        is_admin, 
        created_at, 
        updated_at, 
        last_login_at
    FROM users 
    WHERE {where_clause}
    ORDER BY {sort_by} {sort_order.upper()}
    LIMIT %s OFFSET %s
    """

    params.extend([page_size, offset])
    users = await fetch_all(query, tuple(params))

    logger.info(f"[{request_id}] 사용자 목록 조회 완료 - 총 {total}명")

    return UserListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        users=users
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(request: Request, user_id: int):
    """
    특정 사용자 조회

    - **user_id**: 사용자 ID
    """
    request_id = getattr(request.state, "request_id", "no-id")

    query = """
            SELECT
                id,
                email,
                username,
                is_active,
                is_admin,
                created_at,
                updated_at,
                last_login_at
            FROM users
            WHERE id = %s \
            """

    result = await fetch_one(query, (user_id,))

    if not result:
        logger.warning(f"[{request_id}] 사용자를 찾을 수 없음 - ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    logger.info(f"[{request_id}] 사용자 조회 완료 - ID: {user_id}")
    return result

@router.delete("/{user_id}", response_model=UserDeleteResponse)
async def delete_user(request: Request, user_id: int):
    """
    사용자 삭제

    - **user_id**: 삭제할 사용자 ID

    주의: 실제 삭제되며 복구할 수 없습니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    logger.info(f"[{request_id}] 사용자 삭제 요청 - ID: {user_id}")

    conn = await get_db_connection()

    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 1. 사용자 존재 여부 확인
            check_query = """
                          SELECT id, username, email
                          FROM users
                          WHERE id = %s \
                          """
            await cursor.execute(check_query, (user_id,))
            user = await cursor.fetchone()

            if not user:
                logger.warning(f"[{request_id}] 사용자를 찾을 수 없음 - ID: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다"
                )

            # 2. 사용자 삭제
            delete_query = "DELETE FROM users WHERE id = %s"
            await cursor.execute(delete_query, (user_id,))
            await conn.commit()

            logger.info(
                f"[{request_id}] 사용자 삭제 완료 - "
                f"ID: {user_id}, username: {user['username']}"
            )

            return UserDeleteResponse(
                id=user['id'],
                username=user['username'],
                email=user['email']
            )

    except HTTPException:
        raise
    except Exception as e:
        await conn.rollback()
        logger.error(f"[{request_id}] 사용자 삭제 실패: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 삭제 중 오류가 발생했습니다"
        )
    finally:
        conn.close()

@router.delete("/{user_id}/soft", response_model=UserSoftDeleteResponse)
async def soft_delete_user(request: Request, user_id: int):
    """
    사용자 비활성화 (Soft Delete)

    - **user_id**: 비활성화할 사용자 ID

    물리적으로 삭제하지 않고 is_active를 false로 변경합니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    logger.info(f"[{request_id}] 사용자 비활성화 요청 - ID: {user_id}")

    conn = await get_db_connection()

    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 1. 사용자 존재 여부 확인
            check_query = """
                          SELECT id, username, email, is_active
                          FROM users
                          WHERE id = %s \
                          """
            await cursor.execute(check_query, (user_id,))
            user = await cursor.fetchone()

            if not user:
                logger.warning(f"[{request_id}] 사용자를 찾을 수 없음 - ID: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다"
                )

            # 이미 비활성화된 경우
            if not user['is_active']:
                logger.info(f"[{request_id}] 이미 비활성화된 사용자 - ID: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 비활성화된 사용자입니다"
                )

            # 2. 사용자 비활성화
            update_query = """
                           UPDATE users
                           SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                           WHERE id = %s \
                           """
            await cursor.execute(update_query, (user_id,))
            await conn.commit()

            logger.info(
                f"[{request_id}] 사용자 비활성화 완료 - "
                f"ID: {user_id}, username: {user['username']}"
            )

            return UserDeleteResponse(
                id=user['id'],
                username=user['username'],
                email=user['email'],
                is_active=False
            )

    except HTTPException:
        raise
    except Exception as e:
        await conn.rollback()
        logger.error(f"[{request_id}] 사용자 비활성화 실패: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 비활성화 중 오류가 발생했습니다"
        )
    finally:
        conn.close()


@router.patch("/{user_id}/restore")
async def restore_user(request: Request, user_id: int):
    """
    사용자 복구 (Soft Delete 취소)

    - **user_id**: 복구할 사용자 ID
    """
    request_id = getattr(request.state, "request_id", "no-id")

    logger.info(f"[{request_id}] 사용자 복구 요청 - ID: {user_id}")

    conn = await get_db_connection()

    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 1. 사용자 존재 여부 확인
            check_query = """
                          SELECT id, username, email, is_active
                          FROM users
                          WHERE id = %s \
                          """
            await cursor.execute(check_query, (user_id,))
            user = await cursor.fetchone()

            if not user:
                logger.warning(f"[{request_id}] 사용자를 찾을 수 없음 - ID: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다"
                )

            # 이미 활성화된 경우
            if user['is_active']:
                logger.info(f"[{request_id}] 이미 활성화된 사용자 - ID: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 활성화된 사용자입니다"
                )

            # 2. 사용자 활성화
            update_query = """
                           UPDATE users
                           SET is_active = 1, updated_at = CURRENT_TIMESTAMP
                           WHERE id = %s \
                           """
            await cursor.execute(update_query, (user_id,))
            await conn.commit()

            logger.info(
                f"[{request_id}] 사용자 복구 완료 - "
                f"ID: {user_id}, username: {user['username']}"
            )

            return {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "is_active": True,
                "message": "사용자가 복구되었습니다"
            }

    except HTTPException:
        raise
    except Exception as e:
        await conn.rollback()
        logger.error(f"[{request_id}] 사용자 복구 실패: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 복구 중 오류가 발생했습니다"
        )
    finally:
        conn.close()


@router.put("/{user_id}", response_model=UserUpdateResponse)
async def update_user(request: Request, user_id: int, user_update: UserUpdate):
    """
    사용자 정보 전체 수정 (PUT)

    - **user_id**: 수정할 사용자 ID
    - **email**: 새 이메일 (선택)
    - **username**: 새 사용자명 (선택)
    - **password**: 새 비밀번호 (선택)
    - **is_admin**: 관리자 여부 (선택)

    모든 필드가 선택사항이지만, 최소 1개 이상의 필드를 제공해야 합니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    logger.info(f"[{request_id}] 사용자 수정 요청 - ID: {user_id}")

    # 수정할 필드가 하나도 없는 경우
    if not any([user_update.email, user_update.username, user_update.password, user_update.is_admin is not None]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 필드를 최소 1개 이상 제공해야 합니다"
        )

    conn = await get_db_connection()

    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 1. 사용자 존재 여부 확인
            check_query = "SELECT id FROM users WHERE id = %s"
            await cursor.execute(check_query, (user_id,))
            if not await cursor.fetchone():
                logger.warning(f"[{request_id}] 사용자를 찾을 수 없음 - ID: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다"
                )

            # 2. 이메일 중복 체크 (다른 사용자가 사용 중인지)
            if user_update.email:
                check_email_query = "SELECT id FROM users WHERE email = %s AND id != %s"
                await cursor.execute(check_email_query, (user_update.email, user_id))
                if await cursor.fetchone():
                    logger.warning(f"[{request_id}] 이메일 중복: {user_update.email}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="이미 사용 중인 이메일입니다"
                    )

            # 3. 사용자명 중복 체크 (다른 사용자가 사용 중인지)
            if user_update.username:
                check_username_query = "SELECT id FROM users WHERE username = %s AND id != %s"
                await cursor.execute(check_username_query, (user_update.username, user_id))
                if await cursor.fetchone():
                    logger.warning(f"[{request_id}] 사용자명 중복: {user_update.username}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="이미 사용 중인 사용자명입니다"
                    )

            # 4. UPDATE 쿼리 동적 생성
            update_fields = []
            params = []

            if user_update.email:
                update_fields.append("email = %s")
                params.append(user_update.email)

            if user_update.username:
                update_fields.append("username = %s")
                params.append(user_update.username)

            if user_update.password:
                hashed_password = hash_password(user_update.password)
                update_fields.append("password_hash = %s")
                params.append(hashed_password)

            if user_update.is_admin is not None:
                update_fields.append("is_admin = %s")
                params.append(user_update.is_admin)

            # updated_at은 항상 업데이트
            update_fields.append("updated_at = CURRENT_TIMESTAMP")

            # 5. 사용자 수정
            update_query = f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE id = %s
            """
            params.append(user_id)

            await cursor.execute(update_query, tuple(params))
            await conn.commit()

            # 6. 수정된 사용자 정보 조회
            select_query = """
                           SELECT id, email, username, is_active, is_admin, updated_at
                           FROM users
                           WHERE id = %s \
                           """
            await cursor.execute(select_query, (user_id,))
            updated_user = await cursor.fetchone()

            logger.info(
                f"[{request_id}] 사용자 수정 완료 - "
                f"ID: {user_id}, username: {updated_user['username']}"
            )

            return UserUpdateResponse(**updated_user)

    except HTTPException:
        raise
    except Exception as e:
        await conn.rollback()
        logger.error(f"[{request_id}] 사용자 수정 실패: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 수정 중 오류가 발생했습니다"
        )
    finally:
        conn.close()


@router.patch("/{user_id}", response_model=UserUpdateResponse)
async def partial_update_user(request: Request, user_id: int, user_update: UserUpdate):
    """
    사용자 정보 부분 수정 (PATCH)

    - **user_id**: 수정할 사용자 ID
    - **email**: 새 이메일 (선택)
    - **username**: 새 사용자명 (선택)
    - **password**: 새 비밀번호 (선택)
    - **is_admin**: 관리자 여부 (선택)

    제공된 필드만 수정됩니다.
    """
    # PUT과 동일한 로직 사용
    return await update_user(request, user_id, user_update)