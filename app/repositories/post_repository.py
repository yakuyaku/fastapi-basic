"""
Post repository implementation
app/repositories/post_repository.py
"""
from typing import Optional, List
from app.repositories.base import BaseRepository
from app.domain.entities.post import PostEntity
from app.core.logging import logger


class PostRepository(BaseRepository):
    """
    Post repository implementation

    PostRepositoryProtocol을 구현하며, 게시글 데이터에 대한 모든 데이터베이스 작업을 담당합니다.
    """

    def _to_entity(self, row: Optional[dict]) -> Optional[PostEntity]:
        """
        데이터베이스 row를 PostEntity로 변환

        Args:
            row: 데이터베이스 조회 결과 (dict)

        Returns:
            Optional[PostEntity]: PostEntity 또는 None
        """
        if not row:
            return None

        # is_deleted, is_pinned, is_locked을 boolean으로 변환
        return PostEntity(
            id=row.get('id'),
            title=row.get('title', ''),
            content=row.get('content', ''),
            author_id=row.get('author_id', 0),
            view_count=row.get('view_count', 0),
            like_count=row.get('like_count', 0),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            is_deleted=bool(row.get('is_deleted', 0)),
            is_pinned=bool(row.get('is_pinned', 0)),
            is_locked=bool(row.get('is_locked', 0)),
            password=row.get('password'),
            # JOIN시 작성자 정보
            author_username=row.get('author_username'),
            author_email=row.get('author_email')
        )

    async def create(
            self,
            title: str,
            content: str,
            author_id: int,
            is_pinned: bool = False,
            password: Optional[str] = None
    ) -> PostEntity:
        """게시글 생성"""
        query = """
                INSERT INTO posts (title, content, author_id, is_pinned, is_deleted, password)
                VALUES (%s, %s, %s, %s, 0, %s)
                """
        post_id = await self._execute(
            query,
            (title, content, author_id, 1 if is_pinned else 0, password)
        )

        logger.info(f"Post created in DB - ID: {post_id}, author: {author_id}")

        # 생성된 게시글 조회 및 반환
        return await self.find_by_id(post_id)

    async def find_by_id(self, post_id: int) -> Optional[PostEntity]:
        """ID로 게시글 조회"""
        query = """
                SELECT id, title, content, author_id, view_count, like_count,
                       created_at, updated_at, is_deleted, is_pinned, is_locked, password
                FROM posts
                WHERE id = %s
                """
        row = await self._fetch_one(query, (post_id,))
        return self._to_entity(row)

    async def find_by_id_with_author(self, post_id: int) -> Optional[PostEntity]:
        """ID로 게시글 조회 (작성자 정보 포함)"""
        query = """
                SELECT
                    p.id, p.title, p.content, p.author_id, p.view_count, p.like_count,
                    p.created_at, p.updated_at, p.is_deleted, p.is_pinned, p.is_locked, p.password,
                    u.username as author_username, u.email as author_email
                FROM posts p
                         LEFT JOIN users u ON p.author_id = u.id
                WHERE p.id = %s
                """
        row = await self._fetch_one(query, (post_id,))
        return self._to_entity(row)

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
        # WHERE 조건 동적 생성
        conditions = []
        params = []

        # 삭제된 게시글 제외 (기본값)
        if not include_deleted:
            conditions.append("p.is_deleted = 0")

        # 검색 (제목 또는 내용)
        if search:
            conditions.append("(p.title LIKE %s OR p.content LIKE %s)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        # 작성자 필터
        if author_id is not None:
            conditions.append("p.author_id = %s")
            params.append(author_id)

        # 고정 게시글 필터
        if is_pinned is not None:
            conditions.append("p.is_pinned = %s")
            params.append(1 if is_pinned else 0)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # 허용된 정렬 컬럼 검증
        allowed_sort_columns = ['id', 'title', 'created_at', 'updated_at', 'view_count', 'like_count']
        if sort_by not in allowed_sort_columns:
            sort_by = 'created_at'

        # 정렬 순서 검증
        sort_order = sort_order.upper()
        if sort_order not in ['ASC', 'DESC']:
            sort_order = 'DESC'

        # 전체 개수 조회
        count_query = f"SELECT COUNT(*) as total FROM posts p WHERE {where_clause}"
        count_row = await self._fetch_one(count_query, tuple(params))
        total = count_row['total'] if count_row else 0

        # 게시글 목록 조회 (작성자 정보 포함)
        # 고정 게시글이 먼저 나오도록 정렬
        query = f"""
            SELECT 
                p.id, p.title, p.content, p.author_id, p.view_count, p.like_count,
                p.created_at, p.updated_at, p.is_deleted, p.is_pinned, p.is_locked,
                u.username as author_username, u.email as author_email
            FROM posts p
            LEFT JOIN users u ON p.author_id = u.id
            WHERE {where_clause}
            ORDER BY p.is_pinned DESC, p.{sort_by} {sort_order}
            LIMIT %s OFFSET %s
        """
        params.extend([limit, skip])
        rows = await self._fetch_all(query, tuple(params))

        posts = [self._to_entity(row) for row in rows]

        logger.debug(f"Found {len(posts)} posts (total: {total})")

        return posts, total

    async def update(self, post_id: int, **fields) -> Optional[PostEntity]:
        """
        게시글 정보 업데이트

        Args:
            post_id: 게시글 ID
            **fields: 업데이트할 필드들 (title, content, is_pinned, is_locked 등)

        Returns:
            Optional[PostEntity]: 업데이트된 게시글 엔티티 또는 None
        """
        if not fields:
            return await self.find_by_id(post_id)

        # 허용된 필드 화이트리스트 (SQL Injection 방지)
        ALLOWED_UPDATE_FIELDS = {
            'title', 'content', 'is_pinned', 'is_locked', 'is_deleted'
        }

        # UPDATE 쿼리 동적 생성
        update_fields = []
        params = []

        for field, value in fields.items():
            # 필드명 검증
            if field not in ALLOWED_UPDATE_FIELDS:
                logger.warning(f"Attempted to update disallowed field: {field}")
                raise ValueError(f"허용되지 않은 필드입니다: {field}")

            # boolean 필드 처리
            if field in ['is_pinned', 'is_locked', 'is_deleted']:
                update_fields.append(f"{field} = %s")
                params.append(1 if value else 0)
            else:
                update_fields.append(f"{field} = %s")
                params.append(value)

        # updated_at은 자동 업데이트 (ON UPDATE CURRENT_TIMESTAMP)
        params.append(post_id)

        query = f"""
            UPDATE posts
            SET {', '.join(update_fields)}
            WHERE id = %s
        """

        await self._execute(query, tuple(params))

        logger.info(f"Post updated - ID: {post_id}, fields: {list(fields.keys())}")

        # 업데이트된 게시글 조회 및 반환
        return await self.find_by_id(post_id)

    async def delete(self, post_id: int) -> bool:
        """
        게시글 삭제 (Hard Delete)

        Args:
            post_id: 게시글 ID

        Returns:
            bool: 삭제 성공 여부
        """
        query = "DELETE FROM posts WHERE id = %s"
        rows_affected = await self._execute(query, (post_id,))

        success = rows_affected > 0
        if success:
            logger.info(f"Post hard deleted - ID: {post_id}")

        return success

    async def soft_delete(self, post_id: int) -> bool:
        """
        게시글 비활성화 (Soft Delete)

        Args:
            post_id: 게시글 ID

        Returns:
            bool: 비활성화 성공 여부
        """
        query = """
                UPDATE posts
                SET is_deleted = 1
                WHERE id = %s \
                """
        rows_affected = await self._execute(query, (post_id,))

        success = rows_affected > 0
        if success:
            logger.info(f"Post soft deleted - ID: {post_id}")

        return success

    async def restore(self, post_id: int) -> bool:
        """
        삭제된 게시글 복구

        Args:
            post_id: 게시글 ID

        Returns:
            bool: 복구 성공 여부
        """
        query = """
                UPDATE posts
                SET is_deleted = 0
                WHERE id = %s \
                """
        rows_affected = await self._execute(query, (post_id,))

        success = rows_affected > 0
        if success:
            logger.info(f"Post restored - ID: {post_id}")

        return success

    async def increment_view_count(self, post_id: int) -> None:
        """조회수 증가 (Race Condition 방지)"""
        query = """
                UPDATE posts
                SET view_count = view_count + 1
                WHERE id = %s \
                """
        await self._execute(query, (post_id,))
        logger.debug(f"View count incremented - ID: {post_id}")

    async def increment_like_count(self, post_id: int) -> None:
        """좋아요 수 증가"""
        query = """
                UPDATE posts
                SET like_count = like_count + 1
                WHERE id = %s \
                """
        await self._execute(query, (post_id,))
        logger.debug(f"Like count incremented - ID: {post_id}")

    async def decrement_like_count(self, post_id: int) -> None:
        """좋아요 수 감소"""
        query = """
                UPDATE posts
                SET like_count = GREATEST(like_count - 1, 0)
                WHERE id = %s \
                """
        await self._execute(query, (post_id,))
        logger.debug(f"Like count decremented - ID: {post_id}")

    async def toggle_pin(self, post_id: int) -> bool:
        """
        게시글 고정/고정 해제 토글

        Returns:
            bool: 토글 후 is_pinned 상태
        """
        # 현재 상태 조회
        post = await self.find_by_id(post_id)
        if not post:
            return False

        new_pinned_state = not post.is_pinned

        query = """
                UPDATE posts
                SET is_pinned = %s
                WHERE id = %s \
                """
        await self._execute(query, (1 if new_pinned_state else 0, post_id))

        logger.info(f"Post pin toggled - ID: {post_id}, is_pinned: {new_pinned_state}")
        return new_pinned_state

    async def toggle_lock(self, post_id: int) -> bool:
        """
        게시글 잠금/잠금 해제 토글

        Returns:
            bool: 토글 후 is_locked 상태
        """
        # 현재 상태 조회
        post = await self.find_by_id(post_id)
        if not post:
            return False

        new_locked_state = not post.is_locked

        query = """
                UPDATE posts
                SET is_locked = %s
                WHERE id = %s \
                """
        await self._execute(query, (1 if new_locked_state else 0, post_id))

        logger.info(f"Post lock toggled - ID: {post_id}, is_locked: {new_locked_state}")
        return new_locked_state