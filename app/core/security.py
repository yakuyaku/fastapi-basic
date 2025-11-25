"""
보안 관련 유틸리티 함수
app/core/security.py
"""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import logger

# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    평문 비밀번호와 해시된 비밀번호 비교
    
    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호
    
    Returns:
        bool: 비밀번호 일치 여부
    
    Example:
        is_valid = verify_password("password123", hashed_password)
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    비밀번호 해싱
    
    Args:
        password: 평문 비밀번호
    
    Returns:
        str: 해시된 비밀번호
    
    Example:
        hashed = get_password_hash("password123")
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰 생성
    
    Args:
        data: 토큰에 포함할 데이터 (user_id, email 등)
        expires_delta: 만료 시간 (기본값: 설정에서 가져옴)
    
    Returns:
        str: JWT 토큰
    
    Example:
        token = create_access_token(
            data={"user_id": 1, "email": "user@example.com"},
            expires_delta=timedelta(minutes=15)
        )
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    JWT 토큰 디코딩 및 검증
    
    Args:
        token: JWT 토큰
    
    Returns:
        dict | None: 토큰 페이로드 또는 None (검증 실패 시)
    
    Example:
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("user_id")
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload

    except JWTError as e:
        logger.error(f"JWT 디코딩 실패: {e}")
        return None
    except Exception as e:
        logger.error(f"토큰 검증 중 예상치 못한 에러: {e}")
        return None


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 리프레시 토큰 생성 (옵션)
    
    Args:
        data: 토큰에 포함할 데이터
        expires_delta: 만료 시간 (기본값: 7일)
    
    Returns:
        str: JWT 리프레시 토큰
    
    Example:
        refresh_token = create_refresh_token(
            data={"user_id": 1},
            expires_delta=timedelta(days=7)
        )
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)  # 리프레시 토큰은 7일

    to_encode.update({"exp": expire, "type": "refresh"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt