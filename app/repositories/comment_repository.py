"""
Comment repository implementation
app/repositories/comment_repository.py
"""
from typing import Optional, List
from app.repositories.base import BaseRepository
from app.domain.entities.comment import CommentEntity
from app.core.logging import logger


class CommentRepository(BaseRepository):
    """
    Comment repository implementation

    Tree 구조의 계층형 댓글 시스템 구현
    """

    def _to_entity(self, row: Optional[dict]) -> Optional[CommentEntity]:
        """데이터베이스 row를 CommentEntity로 변환"""
        if not row:
            return None

        return CommentEntity(
            id=row.get('id'),
            post_id=row.get('post_id', 0),
            parent_id=row.get('parent_id'),
            author_id=row.get('author_id', 0),
            content=row.get('content', ''),
            depth=row.get('depth', 0),
            path=row.get('path'),
            order_num=row.get('order_num', 0),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            is_deleted=bool(row.get('is_deleted', 0)),
            password=row.get('password'),
            # JOIN시 작성자 정보
            author_username=row.get('author_username'),
            author_email=row.get('author_email')
        )

    async def create(
            self,
            post_id: int,
            author_id: int,
            content: str,
            parent_id: Optional[int] = None,
            depth: int = 0,
            path: str = "0",  # 기본값 "0" (임시값)
            order_num: int = 0,
            password: Optional[str] = None
    ) -> CommentEntity:
        """댓글 생성"""
        query = """
                INSERT INTO comments (
                    post_id, parent_id, author_id, content,
                    depth, path, order_num, is_deleted, password
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s)
                """
        comment_id = await self._execute(
            query,
            (post_id, parent_id, author_id, content, depth, path, order_num, password)
        )

        logger.info(
            f"Comment created in DB - ID: {comment_id}, post: {post_id}, "
            f"parent: {parent_id}, depth: {depth}, path: {path}"
        )

        return await self.find_by_id(comment_id)

    async def find_by_id(self, comment_id: int) -> Optional[CommentEntity]:
        """ID로 댓글 조회"""
        query = """
                SELECT id, post_id, parent_id, author_id, content,
                       depth, path, order_num, created_at, updated_at, is_deleted, password
                FROM comments
                WHERE id = %s
                """
        row = await self._fetch_one(query, (comment_id,))
        return self._to_entity(row)

    async def find_by_id_with_author(self, comment_id: int) -> Optional[CommentEntity]:
        """ID로 댓글 조회 (작성자 정보 포함)"""
        query = """
                SELECT
                    c.id, c.post_id, c.parent_id, c.author_id, c.content,
                    c.depth, c.path, c.order_num, c.created_at, c.updated_at, c.is_deleted, c.password,
                    u.username as author_username, u.email as author_email
                FROM comments c
                         LEFT JOIN users u ON c.author_id = u.id
                WHERE c.id = %s
                """
        row = await self._fetch_one(query, (comment_id,))
        return self._to_entity(row)

    async def find_by_post_id(
            self,
            post_id: int,
            include_deleted: bool = False
    ) -> List[CommentEntity]:
        """
        게시글 ID로 댓글 목록 조회 (작성자 정보 포함, path 순서)

        Tree 구조를 유지하기 위해 path로 정렬합니다.
        예: path가 "1", "1/2", "1/3", "2", "2/4" 순서로 정렬
        """
        conditions = ["c.post_id = %s"]
        params = [post_id]

        if not include_deleted:
            conditions.append("c.is_deleted = 0")

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT
                c.id, c.post_id, c.parent_id, c.author_id, c.content,
                c.depth, c.path, c.order_num, c.created_at, c.updated_at, c.is_deleted, c.password,
                u.username as author_username, u.email as author_email
            FROM comments c
            LEFT JOIN users u ON c.author_id = u.id
            WHERE {where_clause}
            ORDER BY c.path ASC, c.order_num ASC
        """
        rows = await self._fetch_all(query, tuple(params))
        comments = [self._to_entity(row) for row in rows]

        logger.debug(f"Found {len(comments)} comments for post: {post_id}")

        return comments

    async def find_by_parent_id(
            self,
            parent_id: int,
            include_deleted: bool = False
    ) -> List[CommentEntity]:
        """부모 댓글 ID로 자식 댓글 목록 조회"""
        conditions = ["c.parent_id = %s"]
        params = [parent_id]

        if not include_deleted:
            conditions.append("c.is_deleted = 0")

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT 
                c.id, c.post_id, c.parent_id, c.author_id, c.content,
                c.depth, c.path, c.order_num, c.created_at, c.updated_at, c.is_deleted,
                u.username as author_username, u.email as author_email
            FROM comments c
            LEFT JOIN users u ON c.author_id = u.id
            WHERE {where_clause}
            ORDER BY c.order_num ASC, c.created_at ASC
        """
        rows = await self._fetch_all(query, tuple(params))
        comments = [self._to_entity(row) for row in rows]

        logger.debug(f"Found {len(comments)} child comments for parent: {parent_id}")

        return comments

    async def count_by_post_id(self, post_id: int, include_deleted: bool = False) -> int:
        """게시글의 댓글 개수 조회"""
        conditions = ["post_id = %s"]
        params = [post_id]

        if not include_deleted:
            conditions.append("is_deleted = 0")

        where_clause = " AND ".join(conditions)

        query = f"SELECT COUNT(*) as total FROM comments WHERE {where_clause}"
        row = await self._fetch_one(query, tuple(params))
        return row['total'] if row else 0

    async def count_by_parent_id(self, parent_id: int, include_deleted: bool = False) -> int:
        """특정 댓글의 자식 댓글 개수 조회"""
        conditions = ["parent_id = %s"]
        params = [parent_id]

        if not include_deleted:
            conditions.append("is_deleted = 0")

        where_clause = " AND ".join(conditions)

        query = f"SELECT COUNT(*) as total FROM comments WHERE {where_clause}"
        row = await self._fetch_one(query, tuple(params))
        return row['total'] if row else 0

    async def get_max_order_num(self, post_id: int, parent_id: Optional[int] = None) -> int:
        """
        같은 레벨에서 최대 order_num 조회

        Args:
            post_id: 게시글 ID
            parent_id: 부모 댓글 ID (None이면 최상위 레벨)

        Returns:
            int: 최대 order_num (없으면 0)
        """
        if parent_id is None:
            query = """
                    SELECT COALESCE(MAX(order_num), 0) as max_order
                    FROM comments
                    WHERE post_id = %s AND parent_id IS NULL \
                    """
            params = (post_id,)
        else:
            query = """
                    SELECT COALESCE(MAX(order_num), 0) as max_order
                    FROM comments
                    WHERE post_id = %s AND parent_id = %s \
                    """
            params = (post_id, parent_id)

        row = await self._fetch_one(query, params)
        return row['max_order'] if row else 0

    async def update(self, comment_id: int, **fields) -> Optional[CommentEntity]:
        """댓글 정보 업데이트"""
        if not fields:
            return await self.find_by_id(comment_id)

        # 허용된 필드 화이트리스트 (SQL Injection 방지)
        ALLOWED_UPDATE_FIELDS = {
            'content', 'is_deleted', 'path'
        }

        # UPDATE 쿼리 동적 생성
        update_fields = []
        params = []

        for field, value in fields.items():
            # 필드명 검증
            if field not in ALLOWED_UPDATE_FIELDS:
                logger.warning(f"Attempted to update disallowed field: {field}")
                raise ValueError(f"허용되지 않은 필드입니다: {field}")

            if field in ['is_deleted']:
                update_fields.append(f"{field} = %s")
                params.append(1 if value else 0)
            else:
                update_fields.append(f"{field} = %s")
                params.append(value)

        params.append(comment_id)

        query = f"""
            UPDATE comments
            SET {', '.join(update_fields)}
            WHERE id = %s
        """

        await self._execute(query, tuple(params))

        logger.info(f"Comment updated - ID: {comment_id}, fields: {list(fields.keys())}")

        return await self.find_by_id(comment_id)

    async def soft_delete(self, comment_id: int) -> bool:
        """댓글 소프트 삭제"""
        query = """
                UPDATE comments
                SET is_deleted = 1
                WHERE id = %s \
                """
        rows_affected = await self._execute(query, (comment_id,))

        success = rows_affected > 0
        if success:
            logger.info(f"Comment soft deleted - ID: {comment_id}")

        return success

    async def restore(self, comment_id: int) -> bool:
        """삭제된 댓글 복구"""
        query = """
                UPDATE comments
                SET is_deleted = 0
                WHERE id = %s \
                """
        rows_affected = await self._execute(query, (comment_id,))

        success = rows_affected > 0
        if success:
            logger.info(f"Comment restored - ID: {comment_id}")

        return success

    async def delete(self, comment_id: int) -> bool:
        """댓글 삭제 (Hard Delete)"""
        query = "DELETE FROM comments WHERE id = %s"
        rows_affected = await self._execute(query, (comment_id,))

        success = rows_affected > 0
        if success:
            logger.info(f"Comment hard deleted - ID: {comment_id}")

        return success