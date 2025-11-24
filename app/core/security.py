import bcrypt


def hash_password(password: str) -> str:
    """비밀번호 해싱 (bcrypt 직접 사용)"""
    # 비밀번호를 바이트로 변환
    password_bytes = password.encode('utf-8')

    # bcrypt로 해싱 (자동으로 salt 생성)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    # 문자열로 변환하여 반환
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    # 비밀번호를 바이트로 변환
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')

    # bcrypt로 검증
    return bcrypt.checkpw(password_bytes, hashed_bytes)