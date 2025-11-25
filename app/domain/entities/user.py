"""
User domain entity
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UserEntity:
    """
    User domain entity (순수 비즈니스 객체)

    데이터베이스나 외부 의존성이 없는 순수한 비즈니스 엔티티입니다.
    """
    id: Optional[int] = None
    email: str = ""
    username: str = ""
    password_hash: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    def can_modify(self, target_user_id: int) -> bool:
        """
        대상 사용자를 수정할 수 있는 권한이 있는지 확인

        Args:
            target_user_id: 대상 사용자 ID

        Returns:
            bool: 관리자이거나 본인인 경우 True
        """
        return self.is_admin or self.id == target_user_id

    def can_view(self, target_user_id: int) -> bool:
        """
        대상 사용자 정보를 조회할 수 있는 권한이 있는지 확인

        Args:
            target_user_id: 대상 사용자 ID

        Returns:
            bool: 관리자이거나 본인인 경우 True
        """
        return self.is_admin or self.id == target_user_id
