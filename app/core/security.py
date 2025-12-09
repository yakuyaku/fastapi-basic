import bcrypt
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings


def hash_password(password: str) -> str:
    """
    비밀번호 해싱 (bcrypt)

    Args:
        password: 평문 비밀번호   

    Returns:
        해시된 비밀번호 문자열
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')



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


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증

    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호

    Returns:
        검증 결과 (True/False)
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def generate_random_password(length: int = 8) -> str:
    """
    랜덤 비밀번호 생성

    Args:
        length: 비밀번호 길이 (기본값: 8)

    Returns:
        생성된 랜덤 비밀번호

    Example:
        password = generate_random_password(8)  # "Xy3$kL9p"
    """
    # 대문자, 소문자, 숫자 조합
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT Access Token 생성

    Args:
        data: 토큰에 포함할 데이터 (user_id, username 등)
        expires_delta: 만료 시간 (기본값: 30분)

    Returns:
        JWT 토큰 문자열
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
    JWT Access Token 디코딩

    Args:
        token: JWT 토큰 문자열

    Returns:
        토큰에 포함된 데이터 또는 None (유효하지 않은 경우)
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None