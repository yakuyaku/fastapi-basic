"""
Post domain entity
app/domain/entities/post.py
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PostEntity:
    """
    Post domain entity (순수 비즈니스 객체)

    데이터베이스나 외부 의존성이 없는 순수한 비즈니스 엔티티입니다.
    """
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    author_id: int = 0
    view_count: int = 0
    like_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    is_pinned: bool = False
    is_locked: bool = False
    password: Optional[str] = None  # 게스트 게시글 비밀번호 (해시)

    # JOIN용 작성자 정보 (Optional)
    author_username: Optional[str] = None
    author_email: Optional[str] = None

    def can_modify(self, user_id: int, is_admin: bool) -> bool:
        """
        게시글을 수정할 수 있는 권한이 있는지 확인

        Args:
            user_id: 현재 사용자 ID
            is_admin: 관리자 여부

        Returns:
            bool: 관리자이거나 본인이 작성한 글인 경우 True
        """
        return is_admin or self.author_id == user_id

    def can_delete(self, user_id: int, is_admin: bool) -> bool:
        """
        게시글을 삭제할 수 있는 권한이 있는지 확인

        Args:
            user_id: 현재 사용자 ID
            is_admin: 관리자 여부

        Returns:
            bool: 관리자이거나 본인이 작성한 글인 경우 True
        """
        return is_admin or self.author_id == user_id

    def is_accessible(self) -> bool:
        """
        게시글에 접근 가능한지 확인

        Returns:
            bool: 삭제되지 않은 경우 True
        """
        return not self.is_deleted

    def is_editable(self) -> bool:
        """
        게시글을 편집 가능한지 확인

        Returns:
            bool: 삭제되지 않고 잠기지 않은 경우 True
        """
        return not self.is_deleted and not self.is_locked