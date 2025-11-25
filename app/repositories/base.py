"""
Base repository with common database operations
"""
import aiomysql
from typing import Optional, Dict, Any, List
from app.db.database import get_db_connection


class BaseRepository:
    """
    Base repository class

    공통 데이터베이스 작업을 위한 헬퍼 메서드를 제공합니다.
    모든 repository는 이 클래스를 상속받아 사용합니다.
    """

    async def _fetch_one(
        self,
        query: str,
        params: tuple = ()
    ) -> Optional[Dict[str, Any]]:
        """
        단일 행 조회

        Args:
            query: SQL 쿼리
            params: 쿼리 파라미터

        Returns:
            Optional[Dict[str, Any]]: 조회된 행 (dict 형태) 또는 None
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                return await cursor.fetchone()
        finally:
            conn.close()

    async def _fetch_all(
        self,
        query: str,
        params: tuple = ()
    ) -> List[Dict[str, Any]]:
        """
        여러 행 조회

        Args:
            query: SQL 쿼리
            params: 쿼리 파라미터

        Returns:
            List[Dict[str, Any]]: 조회된 행 목록 (dict 형태)
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                return await cursor.fetchall()
        finally:
            conn.close()

    async def _execute(
        self,
        query: str,
        params: tuple = ()
    ) -> int:
        """
        INSERT/UPDATE/DELETE 쿼리 실행

        Args:
            query: SQL 쿼리
            params: 쿼리 파라미터

        Returns:
            int: INSERT의 경우 새로 생성된 ID (lastrowid),
                 UPDATE/DELETE의 경우 영향받은 행 수 (rowcount)

        Raises:
            Exception: 쿼리 실행 실패 시 (롤백 후 예외 발생)
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                await conn.commit()

                # INSERT의 경우 새로 생성된 ID 반환
                if query.strip().upper().startswith('INSERT'):
                    return cursor.lastrowid
                # UPDATE/DELETE의 경우 영향받은 행 수 반환
                else:
                    return cursor.rowcount
        except Exception as e:
            await conn.rollback()
            raise e
        finally:
            conn.close()
