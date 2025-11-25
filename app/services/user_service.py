"""
User service - Business logic for user operations
"""
from typing import Optional
from fastapi import HTTPException, status
from app.domain.entities.user import UserEntity
from app.domain.interfaces.user_repository import UserRepositoryProtocol
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password
from app.core.logging import logger
import math


class UserService:
    """
    User service

    사용자 관련 비즈니스 로직을 처리합니다.
    - 중복 검사
    - 권한 검증
    - 비밀번호 해싱
    - Repository 조합
    """

    def __init__(self, user_repository: UserRepositoryProtocol):
        """
        Args:
            user_repository: UserRepositoryProtocol을 구현한 repository 인스턴스
        """
        self.repo = user_repository

    async def create_user(self, user_data: UserCreate) -> UserEntity:
        """
        사용자 생성 (비즈니스 로직)

        비즈니스 규칙:
        - 이메일 중복 불가
        - 사용자명 중복 불가
        - 비밀번호 해싱 필수

        Args:
            user_data: 사용자 생성 데이터

        Returns:
            UserEntity: 생성된 사용자 엔티티

        Raises:
            HTTPException: 이메일/사용자명 중복 시
        """
        logger.info(f"Creating user - username: {user_data.username}, email: {user_data.email}")

        # 비즈니스 규칙: 이메일 중복 체크
        existing_user = await self.repo.find_by_email(user_data.email)
        if existing_user:
            logger.warning(f"Email already exists: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 이메일입니다"
            )

        # 비즈니스 규칙: 사용자명 중복 체크
        existing_user = await self.repo.find_by_username(user_data.username)
        if existing_user:
            logger.warning(f"Username already exists: {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 사용자명입니다"
            )

        # 비밀번호 해싱
        password_hash = hash_password(user_data.password)

        # Repository 호출
        user = await self.repo.create(
            email=user_data.email,
            username=user_data.username,
            password_hash=password_hash,
            is_admin=user_data.is_admin
        )

        logger.info(f"User created successfully - ID: {user.id}, username: {user.username}")
        return user

    async def get_user(self, user_id: int, current_user: UserEntity) -> UserEntity:
        """
        사용자 조회 (권한 검증 포함)

        비즈니스 규칙:
        - 본인이거나 관리자만 조회 가능

        Args:
            user_id: 조회할 사용자 ID
            current_user: 현재 인증된 사용자

        Returns:
            UserEntity: 조회된 사용자 엔티티

        Raises:
            HTTPException: 권한 없음 또는 사용자 없음
        """
        # 비즈니스 규칙: 권한 체크
        if not current_user.can_view(user_id):
            logger.warning(
                f"Permission denied - User {current_user.id} tried to view user {user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인의 정보만 조회할 수 있습니다"
            )

        user = await self.repo.find_by_id(user_id)
        if not user:
            logger.warning(f"User not found - ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )

        logger.info(f"User retrieved - ID: {user_id}")
        return user

    async def list_users(
        self,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> dict:
        """
        사용자 목록 조회 (페이징)

        Args:
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지당 항목 수
            search: 검색어
            is_active: 활성 상태 필터
            is_admin: 관리자 필터
            sort_by: 정렬 기준
            sort_order: 정렬 순서

        Returns:
            dict: {users, total, page, page_size, total_pages}
        """
        offset = (page - 1) * page_size

        users, total = await self.repo.find_all(
            skip=offset,
            limit=page_size,
            search=search,
            is_active=is_active,
            is_admin=is_admin,
            sort_by=sort_by,
            sort_order=sort_order
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0

        logger.info(f"Listed {len(users)} users (page {page}/{total_pages}, total: {total})")

        return {
            "users": users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

    async def update_user(
        self,
        user_id: int,
        user_data: UserUpdate,
        current_user: UserEntity
    ) -> UserEntity:
        """
        사용자 정보 수정

        비즈니스 규칙:
        - 본인이거나 관리자만 수정 가능
        - is_admin 변경은 관리자만 가능
        - 이메일/사용자명 중복 불가

        Args:
            user_id: 수정할 사용자 ID
            user_data: 수정할 데이터
            current_user: 현재 인증된 사용자

        Returns:
            UserEntity: 수정된 사용자 엔티티

        Raises:
            HTTPException: 권한 없음, 중복, 사용자 없음
        """
        logger.info(f"Updating user - ID: {user_id}, by user: {current_user.id}")

        # 비즈니스 규칙: 권한 체크
        if not current_user.can_modify(user_id):
            logger.warning(
                f"Permission denied - User {current_user.id} tried to modify user {user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인의 정보만 수정할 수 있습니다"
            )

        # 비즈니스 규칙: is_admin 변경은 관리자만 가능
        if user_data.is_admin is not None and not current_user.is_admin:
            logger.warning(
                f"Permission denied - User {current_user.id} tried to change admin status"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="관리자 권한 변경은 관리자만 가능합니다"
            )

        # 사용자 존재 확인
        existing_user = await self.repo.find_by_id(user_id)
        if not existing_user:
            logger.warning(f"User not found - ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )

        # 비즈니스 규칙: 이메일 중복 체크 (다른 사용자가 사용 중인지)
        if user_data.email:
            email_user = await self.repo.find_by_email(user_data.email)
            if email_user and email_user.id != user_id:
                logger.warning(f"Email already exists: {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 사용 중인 이메일입니다"
                )

        # 비즈니스 규칙: 사용자명 중복 체크 (다른 사용자가 사용 중인지)
        if user_data.username:
            username_user = await self.repo.find_by_username(user_data.username)
            if username_user and username_user.id != user_id:
                logger.warning(f"Username already exists: {user_data.username}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 사용 중인 사용자명입니다"
                )

        # 업데이트할 필드 준비
        update_data = user_data.model_dump(exclude_unset=True)

        # 비밀번호가 있으면 해싱
        if 'password' in update_data:
            update_data['password_hash'] = hash_password(update_data.pop('password'))

        # 수정할 필드가 없으면 현재 상태 반환
        if not update_data:
            logger.info(f"No fields to update - ID: {user_id}")
            return existing_user

        # Repository 업데이트 호출
        updated_user = await self.repo.update(user_id, **update_data)

        logger.info(f"User updated successfully - ID: {user_id}")
        return updated_user

    async def delete_user(self, user_id: int, current_user: UserEntity) -> UserEntity:
        """
        사용자 삭제 (Hard Delete)

        비즈니스 규칙:
        - 자기 자신은 삭제할 수 없음

        Args:
            user_id: 삭제할 사용자 ID
            current_user: 현재 인증된 사용자 (관리자)

        Returns:
            UserEntity: 삭제된 사용자 엔티티

        Raises:
            HTTPException: 자기 자신 삭제 시도, 사용자 없음
        """
        logger.info(f"Deleting user - ID: {user_id}, by admin: {current_user.id}")

        # 비즈니스 규칙: 자기 자신은 삭제할 수 없음
        if user_id == current_user.id:
            logger.warning(f"Self-deletion attempt - ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="자기 자신은 삭제할 수 없습니다"
            )

        # 사용자 존재 확인
        user = await self.repo.find_by_id(user_id)
        if not user:
            logger.warning(f"User not found - ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )

        # 삭제 수행
        success = await self.repo.delete(user_id)
        if not success:
            logger.error(f"Failed to delete user - ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 삭제 중 오류가 발생했습니다"
            )

        logger.info(f"User deleted successfully - ID: {user_id}")
        return user

    async def soft_delete_user(self, user_id: int, current_user: UserEntity) -> UserEntity:
        """
        사용자 비활성화 (Soft Delete)

        비즈니스 규칙:
        - 자기 자신은 비활성화할 수 없음
        - 이미 비활성화된 사용자는 에러

        Args:
            user_id: 비활성화할 사용자 ID
            current_user: 현재 인증된 사용자 (관리자)

        Returns:
            UserEntity: 비활성화된 사용자 엔티티

        Raises:
            HTTPException: 자기 자신 비활성화 시도, 이미 비활성화된 경우, 사용자 없음
        """
        logger.info(f"Soft deleting user - ID: {user_id}, by admin: {current_user.id}")

        # 비즈니스 규칙: 자기 자신은 비활성화할 수 없음
        if user_id == current_user.id:
            logger.warning(f"Self-deactivation attempt - ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="자기 자신은 비활성화할 수 없습니다"
            )

        # 사용자 존재 확인
        user = await self.repo.find_by_id(user_id)
        if not user:
            logger.warning(f"User not found - ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )

        # 비즈니스 규칙: 이미 비활성화된 경우
        if not user.is_active:
            logger.info(f"User already deactivated - ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 비활성화된 사용자입니다"
            )

        # 비활성화 수행
        success = await self.repo.soft_delete(user_id)
        if not success:
            logger.error(f"Failed to soft delete user - ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 비활성화 중 오류가 발생했습니다"
            )

        # 업데이트된 사용자 조회
        updated_user = await self.repo.find_by_id(user_id)

        logger.info(f"User soft deleted successfully - ID: {user_id}")
        return updated_user

    async def restore_user(self, user_id: int) -> UserEntity:
        """
        비활성화된 사용자 복구

        비즈니스 규칙:
        - 이미 활성화된 사용자는 에러

        Args:
            user_id: 복구할 사용자 ID

        Returns:
            UserEntity: 복구된 사용자 엔티티

        Raises:
            HTTPException: 이미 활성화된 경우, 사용자 없음
        """
        logger.info(f"Restoring user - ID: {user_id}")

        # 사용자 존재 확인
        user = await self.repo.find_by_id(user_id)
        if not user:
            logger.warning(f"User not found - ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )

        # 비즈니스 규칙: 이미 활성화된 경우
        if user.is_active:
            logger.info(f"User already active - ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 활성화된 사용자입니다"
            )

        # 복구 수행
        success = await self.repo.restore(user_id)
        if not success:
            logger.error(f"Failed to restore user - ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 복구 중 오류가 발생했습니다"
            )

        # 업데이트된 사용자 조회
        restored_user = await self.repo.find_by_id(user_id)

        logger.info(f"User restored successfully - ID: {user_id}")
        return restored_user
