"""
데이터베이스 연결 및 쿼리 실행
app/db/database.py
"""

import aiomysql
from typing import Dict, List, Any, Optional
from app.core.config import settings

async def get_db_connection():
    """
    데이터베이스 연결 생성
    
    Returns:
        aiomysql.Connection: MySQL 연결 객체
    """
    conn = await aiomysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        db=settings.DB_NAME,
        charset='utf8mb4',
        autocommit=False
    )
    return conn


async def fetch_one(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """
    단일 행 조회 (SELECT)
    
    Args:
        query: SQL 쿼리
        params: 쿼리 파라미터
    
    Returns:
        dict | None: 조회된 행 (없으면 None)
    
    Example:
        user = await fetch_one("SELECT * FROM users WHERE id = %s", (1,))
    """
    conn = await get_db_connection()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, params)
            result = await cursor.fetchone()
            return result
    finally:
        conn.close()


async def fetch_all(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """
    여러 행 조회 (SELECT)
    
    Args:
        query: SQL 쿼리
        params: 쿼리 파라미터
    
    Returns:
        list[dict]: 조회된 행 목록
    
    Example:
        users = await fetch_all("SELECT * FROM users WHERE is_active = %s", (True,))
    """
    conn = await get_db_connection()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, params)
            result = await cursor.fetchall()
            return result
    finally:
        conn.close()


async def execute_query(query: str, params: tuple = ()) -> int:
    """
    INSERT/UPDATE/DELETE 쿼리 실행
    
    Args:
        query: SQL 쿼리
        params: 쿼리 파라미터
    
    Returns:
        int: INSERT의 경우 새로 생성된 ID, UPDATE/DELETE의 경우 영향받은 행 수
    
    Example:
        # INSERT
        user_id = await execute_query(
            "INSERT INTO users (username, email) VALUES (%s, %s)",
            ("john", "john@example.com")
        )
        
        # UPDATE
        rows = await execute_query(
            "UPDATE users SET is_active = %s WHERE id = %s",
            (False, 1)
        )
        
        # DELETE
        rows = await execute_query("DELETE FROM users WHERE id = %s", (1,))
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


async def execute_update(query: str, params: tuple = ()) -> int:
    """
    INSERT/UPDATE/DELETE 쿼리 실행 (execute_query의 별칭)
    
    Args:
        query: SQL 쿼리
        params: 쿼리 파라미터
    
    Returns:
        int: 영향받은 행 수 또는 INSERT ID
    """
    return await execute_query(query, params)


async def execute_many(query: str, params_list: List[tuple]) -> int:
    """
    여러 개의 INSERT/UPDATE/DELETE 쿼리를 배치로 실행
    
    Args:
        query: SQL 쿼리
        params_list: 쿼리 파라미터 리스트
    
    Returns:
        int: 영향받은 총 행 수
    
    Example:
        users = [
            ("john", "john@example.com"),
            ("jane", "jane@example.com"),
        ]
        rows = await execute_many(
            "INSERT INTO users (username, email) VALUES (%s, %s)",
            users
        )
    """
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.executemany(query, params_list)
            await conn.commit()
            return cursor.rowcount
    except Exception as e:
        await conn.rollback()
        raise e
    finally:
        conn.close()


async def test_connection() -> bool:
    """
    데이터베이스 연결 테스트
    
    Returns:
        bool: 연결 성공 여부
    """
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT 1")
            result = await cursor.fetchone()
        conn.close()
        return result[0] == 1
    except Exception as e:
        print(f"데이터베이스 연결 실패: {e}")
        return False