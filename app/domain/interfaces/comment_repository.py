"""
Comment repository protocol (interface)
app/domain/interfaces/comment_repository.py
"""
from typing import Protocol, Optional, List
from app.domain.entities.comment import CommentEntity


class CommentRepositoryProtocol(Protocol):
    """Comment repository 인터페이스"""

    async def create(
            self,
            post_id: int,
            author_id: int,
            content: str,
            parent_id: Optional[int] = None,
            depth: int = 0,
            path: str = "0",
            order_num: int = 0
    ) -> CommentEntity:
        """댓글 생성"""
        ...

    async def find_by_id(self, comment_id: int) -> Optional[CommentEntity]:
        """ID로 댓글 조회"""
        ...

    async def find_by_id_with_author(self, comment_id: int) -> Optional[CommentEntity]:
        """ID로 댓글 조회 (작성자 정보 포함)"""
        ...

    async def find_by_post_id(
            self,
            post_id: int,
            include_deleted: bool = False
    ) -> List[CommentEntity]:
        """게시글 ID로 댓글 목록 조회 (작성자 정보 포함, path 순서)"""
        ...

    async def find_by_parent_id(
            self,
            parent_id: int,
            include_deleted: bool = False
    ) -> List[CommentEntity]:
        """부모 댓글 ID로 자식 댓글 목록 조회"""
        ...

    async def count_by_post_id(self, post_id: int, include_deleted: bool = False) -> int:
        """게시글의 댓글 개수 조회"""
        ...

    async def count_by_parent_id(self, parent_id: int, include_deleted: bool = False) -> int:
        """특정 댓글의 자식 댓글 개수 조회"""
        ...

    async def get_max_order_num(self, post_id: int, parent_id: Optional[int] = None) -> int:
        """같은 레벨에서 최대 order_num 조회"""
        ...

    async def update(self, comment_id: int, **fields) -> Optional[CommentEntity]:
        """댓글 정보 업데이트"""
        ...

    async def soft_delete(self, comment_id: int) -> bool:
        """댓글 소프트 삭제"""
        ...

    async def restore(self, comment_id: int) -> bool:
        """삭제된 댓글 복구"""
        ...

    async def delete(self, comment_id: int) -> bool:
        """댓글 삭제 (Hard Delete)"""
        ...