"""
Comment domain entity
app/domain/entities/comment.py
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class CommentEntity:
    """
    Comment domain entity (순수 비즈니스 객체)

    Tree 구조의 계층형 댓글 시스템:
    - path: 계층 경로 (예: "1/3/5" → 1번의 자식 3번의 자식 5번)
    - depth: 댓글 깊이 (0: 최상위, 1: 1차 대댓글, 2: 2차 대댓글...)
    - parent_id: 부모 댓글 ID (None이면 최상위 댓글)
    - order_num: 같은 레벨에서의 정렬 순서
    """
    id: Optional[int] = None
    post_id: int = 0
    parent_id: Optional[int] = None
    author_id: int = 0
    content: str = ""
    depth: int = 0
    path: Optional[str] = None
    order_num: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    password: Optional[str] = None  # 게스트 댓글 비밀번호 (해시)

    # JOIN용 작성자 정보 (Optional)
    author_username: Optional[str] = None
    author_email: Optional[str] = None

    # Tree 구조용 (Response에서 사용)
    children: List['CommentEntity'] = None

    def __post_init__(self):
        """dataclass 초기화 후 처리"""
        if self.children is None:
            self.children = []

    def can_modify(self, user_id: int, is_admin: bool) -> bool:
        """
        댓글을 수정할 수 있는 권한이 있는지 확인

        Args:
            user_id: 현재 사용자 ID
            is_admin: 관리자 여부

        Returns:
            bool: 관리자이거나 본인이 작성한 댓글인 경우 True
        """
        return is_admin or self.author_id == user_id

    def can_delete(self, user_id: int, is_admin: bool) -> bool:
        """
        댓글을 삭제할 수 있는 권한이 있는지 확인

        Args:
            user_id: 현재 사용자 ID
            is_admin: 관리자 여부

        Returns:
            bool: 관리자이거나 본인이 작성한 댓글인 경우 True
        """
        return is_admin or self.author_id == user_id

    def is_root_comment(self) -> bool:
        """최상위 댓글인지 확인"""
        return self.parent_id is None and self.depth == 0

    def is_reply(self) -> bool:
        """대댓글인지 확인"""
        return self.parent_id is not None and self.depth > 0

    def get_path_list(self) -> List[int]:
        """
        path를 리스트로 변환
        예: "1/3/5" → [1, 3, 5]
        """
        if not self.path:
            return []
        return [int(x) for x in self.path.split('/') if x]

    def build_path(self, parent_path: Optional[str], comment_id: int) -> str:
        """
        새로운 path 생성

        Args:
            parent_path: 부모 댓글의 path
            comment_id: 현재 댓글 ID

        Returns:
            str: 새로운 path (예: "1/3/5")
        """
        if not parent_path:
            return str(comment_id)
        return f"{parent_path}/{comment_id}"

    def add_child(self, child: 'CommentEntity') -> None:
        """자식 댓글 추가 (Tree 구조 생성용)"""
        if self.children is None:
            self.children = []
        self.children.append(child)

    def has_children(self) -> bool:
        """자식 댓글이 있는지 확인"""
        return self.children is not None and len(self.children) > 0