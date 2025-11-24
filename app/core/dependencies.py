from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.db.database import execute_query
from app.core.logging import logger

# Bearer 토큰 스키마
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    현재 인증된 사용자 가져오기

    JWT 토큰을 검증하고 사용자 정보를 반환합니다.
    """
    token = credentials.credentials

    # 토큰 디코딩
    payload = decode_access_token(token)

    if payload is None:
        logger.warning("유효하지 않은 토큰")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: int = payload.get("user_id")

    if user_id is None:
        logger.warning("토큰에 user_id가 없음")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 사용자 조회
    query = """
            SELECT id, email, username, is_active, is_admin, created_at
            FROM users
            WHERE id = %s \
            """
    result = await execute_query(query, (user_id,))

    if not result:
        logger.warning(f"사용자를 찾을 수 없음 - ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = result[0]

    # 비활성화된 사용자 체크
    if not user['is_active']:
        logger.warning(f"비활성화된 사용자 - ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )

    return user


async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    """
    현재 인증된 관리자 사용자 가져오기

    관리자 권한이 필요한 엔드포인트에 사용합니다.
    """
    if not current_user['is_admin']:
        logger.warning(f"관리자 권한 필요 - 사용자 ID: {current_user['id']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )

    return current_user