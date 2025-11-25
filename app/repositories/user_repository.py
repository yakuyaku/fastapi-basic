"""
User repository implementation
"""
from typing import Optional, List
from app.repositories.base import BaseRepository
from app.domain.entities.user import UserEntity
from app.core.logging import logger


class UserRepository(BaseRepository):
    """
    User repository implementation

    UserRepositoryProtocol을 구현하며, 사용자 데이터에 대한 모든 데이터베이스 작업을 담당합니다.
    """

    def _to_entity(self, row: Optional[dict]) -> Optional[UserEntity]:
        """
        데이터베이스 row를 UserEntity로 변환

        Args:
            row: 데이터베이스 조회 결과 (dict)

        Returns:
            Optional[UserEntity]: UserEntity 또는 None
        """
        if not row:
            return None
        return UserEntity(**row)

    async def create(
        self,
        email: str,
        username: str,
        password_hash: str,
        is_admin: bool = False
    ) -> UserEntity:
        """사용자 생성"""
        query = """
            INSERT INTO users (email, username, password_hash, is_admin, is_active)
            VALUES (%s, %s, %s, %s, 1)
        """
        user_id = await self._execute(query, (email, username, password_hash, is_admin))

        logger.info(f"User created in DB - ID: {user_id}, username: {username}")

        # 생성된 사용자 조회 및 반환
        return await self.find_by_id(user_id)

    async def find_by_id(self, user_id: int) -> Optional[UserEntity]:
        """ID로 사용자 조회"""
        query = """
            SELECT id, email, username, password_hash, is_active, is_admin,
                   created_at, updated_at, last_login_at
            FROM users
            WHERE id = %s
        """
        row = await self._fetch_one(query, (user_id,))
        return self._to_entity(row)

    async def find_by_email(self, email: str) -> Optional[UserEntity]:
        """이메일로 사용자 조회"""
        query = """
            SELECT id, email, username, password_hash, is_active, is_admin,
                   created_at, updated_at, last_login_at
            FROM users
            WHERE email = %s
        """
        row = await self._fetch_one(query, (email,))
        return self._to_entity(row)

    async def find_by_username(self, username: str) -> Optional[UserEntity]:
        """사용자명으로 사용자 조회"""
        query = """
            SELECT id, email, username, password_hash, is_active, is_admin,
                   created_at, updated_at, last_login_at
            FROM users
            WHERE username = %s
        """
        row = await self._fetch_one(query, (username,))
        return self._to_entity(row)

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

        Returns:
            tuple[List[UserEntity], int]: (사용자 목록, 전체 개수)
        """
        # WHERE 조건 동적 생성
        conditions = []
        params = []

        if search:
            conditions.append("(username LIKE %s OR email LIKE %s)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(1 if is_active else 0)

        if is_admin is not None:
            conditions.append("is_admin = %s")
            params.append(1 if is_admin else 0)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # 허용된 정렬 컬럼 검증
        allowed_sort_columns = ['id', 'username', 'email', 'created_at', 'updated_at']
        if sort_by not in allowed_sort_columns:
            sort_by = 'created_at'

        # 정렬 순서 검증
        sort_order = sort_order.upper()
        if sort_order not in ['ASC', 'DESC']:
            sort_order = 'DESC'

        # 전체 개수 조회
        count_query = f"SELECT COUNT(*) as total FROM users WHERE {where_clause}"
        count_row = await self._fetch_one(count_query, tuple(params))
        total = count_row['total'] if count_row else 0

        # 사용자 목록 조회
        query = f"""
            SELECT id, email, username, password_hash, is_active, is_admin,
                   created_at, updated_at, last_login_at
            FROM users
            WHERE {where_clause}
            ORDER BY {sort_by} {sort_order}
            LIMIT %s OFFSET %s
        """
        params.extend([limit, skip])
        rows = await self._fetch_all(query, tuple(params))

        users = [self._to_entity(row) for row in rows]

        logger.debug(f"Found {len(users)} users (total: {total})")

        return users, total

    async def update(self, user_id: int, **fields) -> Optional[UserEntity]:
        """
        사용자 정보 업데이트

        Args:
            user_id: 사용자 ID
            **fields: 업데이트할 필드들 (email, username, password_hash, is_admin 등)

        Returns:
            Optional[UserEntity]: 업데이트된 사용자 엔티티 또는 None
        """
        if not fields:
            return await self.find_by_id(user_id)

        # UPDATE 쿼리 동적 생성
        update_fields = []
        params = []

        for field, value in fields.items():
            update_fields.append(f"{field} = %s")
            params.append(value)

        # updated_at은 항상 업데이트
        update_fields.append("updated_at = CURRENT_TIMESTAMP")

        params.append(user_id)

        query = f"""
            UPDATE users
            SET {', '.join(update_fields)}
            WHERE id = %s
        """

        await self._execute(query, tuple(params))

        logger.info(f"User updated - ID: {user_id}, fields: {list(fields.keys())}")

        # 업데이트된 사용자 조회 및 반환
        return await self.find_by_id(user_id)

    async def delete(self, user_id: int) -> bool:
        """
        사용자 삭제 (Hard Delete)

        Args:
            user_id: 사용자 ID

        Returns:
            bool: 삭제 성공 여부
        """
        query = "DELETE FROM users WHERE id = %s"
        rows_affected = await self._execute(query, (user_id,))

        success = rows_affected > 0
        if success:
            logger.info(f"User hard deleted - ID: {user_id}")

        return success

    async def soft_delete(self, user_id: int) -> bool:
        """
        사용자 비활성화 (Soft Delete)

        Args:
            user_id: 사용자 ID

        Returns:
            bool: 비활성화 성공 여부
        """
        query = """
            UPDATE users
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        rows_affected = await self._execute(query, (user_id,))

        success = rows_affected > 0
        if success:
            logger.info(f"User soft deleted - ID: {user_id}")

        return success

    async def restore(self, user_id: int) -> bool:
        """
        비활성화된 사용자 복구

        Args:
            user_id: 사용자 ID

        Returns:
            bool: 복구 성공 여부
        """
        query = """
            UPDATE users
            SET is_active = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        rows_affected = await self._execute(query, (user_id,))

        success = rows_affected > 0
        if success:
            logger.info(f"User restored - ID: {user_id}")

        return success

    async def update_last_login(self, user_id: int) -> None:
        """마지막 로그인 시간 업데이트"""
        query = """
            UPDATE users
            SET last_login_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        await self._execute(query, (user_id,))

        logger.debug(f"Last login updated - ID: {user_id}")
