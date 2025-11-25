"""
Auth service - Business logic for authentication
"""
from fastapi import HTTPException, status
from app.domain.entities.user import UserEntity
from app.domain.interfaces.user_repository import UserRepositoryProtocol
from app.schemas.auth import LoginRequest
from app.core.security import verify_password, create_access_token
from app.core.logging import logger


class AuthService:
    """
    Auth service

    인증 관련 비즈니스 로직을 처리합니다.
    - 로그인 검증
    - 토큰 생성
    - 마지막 로그인 업데이트
    """

    def __init__(self, user_repository: UserRepositoryProtocol):
        """
        Args:
            user_repository: UserRepositoryProtocol을 구현한 repository 인스턴스
        """
        self.repo = user_repository

    async def login(self, login_data: LoginRequest) -> tuple[str, UserEntity]:
        """
        로그인 처리

        비즈니스 규칙:
        - 이메일과 비밀번호가 일치해야 함
        - 활성화된 계정만 로그인 가능
        - 로그인 성공 시 마지막 로그인 시간 업데이트

        Args:
            login_data: 로그인 요청 데이터 (email, password)

        Returns:
            tuple[str, UserEntity]: (JWT 토큰, 사용자 엔티티)

        Raises:
            HTTPException: 인증 실패, 비활성화된 계정
        """
        logger.info(f"Login attempt - email: {login_data.email}")

        # 사용자 조회
        user = await self.repo.find_by_email(login_data.email)

        # 비즈니스 규칙: 이메일/비밀번호 검증
        if not user or not verify_password(login_data.password, user.password_hash):
            logger.warning(f"Login failed - invalid credentials for email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다"
            )

        # 비즈니스 규칙: 활성 상태 체크
        if not user.is_active:
            logger.warning(f"Login failed - inactive account: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 계정입니다"
            )

        # 마지막 로그인 시간 업데이트
        await self.repo.update_last_login(user.id)

        # JWT 토큰 생성
        token = create_access_token(
            data={
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            }
        )

        logger.info(f"Login successful - ID: {user.id}, username: {user.username}")

        return token, user
