"""
User repository interface (Protocol)
"""
from typing import Protocol, Optional, List
from app.domain.entities.user import UserEntity


class UserRepositoryProtocol(Protocol):
    """
    User repository interface

    Service 계층은 이 인터페이스에 의존하며, 구현체는 Repository 계층에서 제공됩니다.
    이를 통해 의존성 역전 원칙(Dependency Inversion Principle)을 준수합니다.
    """

    async def create(
        self,
        email: str,
        username: str,
        password_hash: str,
        is_admin: bool = False
    ) -> UserEntity:
        """
        새 사용자 생성

        Args:
            email: 이메일
            username: 사용자명
            password_hash: 해시된 비밀번호
            is_admin: 관리자 여부

        Returns:
            UserEntity: 생성된 사용자 엔티티
        """
        ...

    async def find_by_id(self, user_id: int) -> Optional[UserEntity]:
        """
        ID로 사용자 조회

        Args:
            user_id: 사용자 ID

        Returns:
            Optional[UserEntity]: 사용자 엔티티 또는 None
        """
        ...

    async def find_by_email(self, email: str) -> Optional[UserEntity]:
        """
        이메일로 사용자 조회

        Args:
            email: 이메일

        Returns:
            Optional[UserEntity]: 사용자 엔티티 또는 None
        """
        ...

    async def find_by_username(self, username: str) -> Optional[UserEntity]:
        """
        사용자명으로 사용자 조회

        Args:
            username: 사용자명

        Returns:
            Optional[UserEntity]: 사용자 엔티티 또는 None
        """
        ...

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[UserEntity], int]:
        """
        사용자 목록 조회 (페이징, 검색, 필터링, 정렬)

        Args:
            skip: 건너뛸 개수 (offset)
            limit: 가져올 개수
            search: 검색어 (username 또는 email)
            is_active: 활성 상태 필터
            is_admin: 관리자 필터
            sort_by: 정렬 기준 컬럼
            sort_order: 정렬 순서 (asc/desc)

        Returns:
            tuple[List[UserEntity], int]: (사용자 목록, 전체 개수)
        """
        ...

    async def update(self, user_id: int, **fields) -> Optional[UserEntity]:
        """
        사용자 정보 업데이트

        Args:
            user_id: 사용자 ID
            **fields: 업데이트할 필드들

        Returns:
            Optional[UserEntity]: 업데이트된 사용자 엔티티 또는 None
        """
        ...

    async def delete(self, user_id: int) -> bool:
        """
        사용자 삭제 (Hard Delete)

        Args:
            user_id: 사용자 ID

        Returns:
            bool: 삭제 성공 여부
        """
        ...

    async def soft_delete(self, user_id: int) -> bool:
        """
        사용자 비활성화 (Soft Delete)

        Args:
            user_id: 사용자 ID

        Returns:
            bool: 비활성화 성공 여부
        """
        ...

    async def restore(self, user_id: int) -> bool:
        """
        비활성화된 사용자 복구

        Args:
            user_id: 사용자 ID

        Returns:
            bool: 복구 성공 여부
        """
        ...

    async def update_last_login(self, user_id: int) -> None:
        """
        마지막 로그인 시간 업데이트

        Args:
            user_id: 사용자 ID
        """
        ...
