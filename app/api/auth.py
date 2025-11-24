from fastapi import APIRouter, HTTPException, status, Request, Depends
from datetime import datetime
from app.schemas.auth import LoginRequest, LoginResponse
from app.core.security import verify_password, create_access_token
from app.db.database import get_db_connection, execute_query
from app.core.logging import logger
from app.core.dependencies import get_current_user
import aiomysql

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, login_data: LoginRequest):
    """
    로그인

    - **email**: 이메일 주소
    - **password**: 비밀번호

    성공 시 JWT Access Token을 반환합니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    logger.info(f"[{request_id}] 로그인 요청 - email: {login_data.email}")

    conn = await get_db_connection()

    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 사용자 조회
            query = """
                    SELECT id, email, username, password_hash, is_active, is_admin, created_at
                    FROM users
                    WHERE email = %s \
                    """
            await cursor.execute(query, (login_data.email,))
            user = await cursor.fetchone()

            # 사용자가 없거나 비밀번호가 틀린 경우
            if not user or not verify_password(login_data.password, user['password_hash']):
                logger.warning(f"[{request_id}] 로그인 실패 - email: {login_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="이메일 또는 비밀번호가 올바르지 않습니다"
                )

            # 비활성화된 계정 체크
            if not user['is_active']:
                logger.warning(f"[{request_id}] 비활성화된 계정 로그인 시도 - ID: {user['id']}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="비활성화된 계정입니다"
                )

            # 마지막 로그인 시간 업데이트
            update_query = """
                           UPDATE users
                           SET last_login_at = CURRENT_TIMESTAMP
                           WHERE id = %s \
                           """
            await cursor.execute(update_query, (user['id'],))
            await conn.commit()

            # JWT 토큰 생성
            access_token = create_access_token(
                data={
                    "user_id": user['id'],
                    "username": user['username'],
                    "email": user['email']
                }
            )

            logger.info(f"[{request_id}] 로그인 성공 - ID: {user['id']}, username: {user['username']}")

            return LoginResponse(
                access_token=access_token,
                token_type="bearer",
                user={
                    "id": user['id'],
                    "email": user['email'],
                    "username": user['username'],
                    "is_admin": user['is_admin']
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] 로그인 처리 실패: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다"
        )
    finally:
        conn.close()


@router.get("/me")
async def get_me(request: Request, current_user: dict = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회

    JWT 토큰이 필요합니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    logger.info(f"[{request_id}] 현재 사용자 조회 - ID: {current_user['id']}")

    return {
        "id": current_user['id'],
        "email": current_user['email'],
        "username": current_user['username'],
        "is_active": current_user['is_active'],
        "is_admin": current_user['is_admin'],
        "created_at": current_user['created_at']
    }


@router.post("/logout")
async def logout(request: Request, current_user: dict = Depends(get_current_user)):
    """
    로그아웃

    클라이언트에서 토큰을 삭제하도록 안내합니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    logger.info(f"[{request_id}] 로그아웃 - ID: {current_user['id']}")

    return {
        "message": "로그아웃되었습니다. 클라이언트에서 토큰을 삭제해주세요."
    }