"""
Post repository protocol (interface)
app/domain/interfaces/post_repository.py
"""
from typing import Protocol, Optional, List
from app.domain.entities.post import PostEntity


class PostRepositoryProtocol(Protocol):
    """
    Post repository 인터페이스

    의존성 역전 원칙(DIP)을 위한 Protocol 정의
    Service는 이 인터페이스에 의존하며, Repository는 이를 구현합니다.
    """

    async def create(
            self,
            title: str,
            content: str,
            author_id: int,
            is_pinned: bool = False
    ) -> PostEntity:
        """게시글 생성"""
        ...

    async def find_by_id(self, post_id: int) -> Optional[PostEntity]:
        """ID로 게시글 조회"""
        ...

    async def find_by_id_with_author(self, post_id: int) -> Optional[PostEntity]:
        """ID로 게시글 조회 (작성자 정보 포함)"""
        ...

    async def find_all(
            self,
            skip: int = 0,
            limit: int = 100,
            search: Optional[str] = None,
            author_id: Optional[int] = None,
            is_pinned: Optional[bool] = None,
            include_deleted: bool = False,
            sort_by: str = "created_at",
            sort_order: str = "desc"
    ) -> tuple[List[PostEntity], int]:
        """
        게시글 목록 조회 (페이징, 검색, 필터링, 정렬)

        Returns:
            tuple[List[PostEntity], int]: (게시글 목록, 전체 개수)
        """
        ...

    async def update(self, post_id: int, **fields) -> Optional[PostEntity]:
        """게시글 정보 업데이트"""
        ...

    async def delete(self, post_id: int) -> bool:
        """게시글 삭제 (Hard Delete)"""
        ...

    async def soft_delete(self, post_id: int) -> bool:
        """게시글 비활성화 (Soft Delete)"""
        ...

    async def restore(self, post_id: int) -> bool:
        """삭제된 게시글 복구"""
        ...

    async def increment_view_count(self, post_id: int) -> None:
        """조회수 증가"""
        ...

    async def increment_like_count(self, post_id: int) -> None:
        """좋아요 수 증가"""
        ...

    async def decrement_like_count(self, post_id: int) -> None:
        """좋아요 수 감소"""
        ...

    async def toggle_pin(self, post_id: int) -> bool:
        """게시글 고정/고정 해제 토글"""
        ...

    async def toggle_lock(self, post_id: int) -> bool:
        """게시글 잠금/잠금 해제 토글"""
        ...