import aiomysql
from app.core.config import settings


async def get_db_connection():
    """데이터베이스 연결 생성"""
    conn = await aiomysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        db=settings.DB_NAME,
        charset='utf8mb4'
    )
    return conn


async def execute_query(query: str, params: tuple = None):
    """SELECT 쿼리 실행"""
    conn = await get_db_connection()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, params or ())
            result = await cursor.fetchall()
            return result
    finally:
        conn.close()


async def execute_update(query: str, params: tuple = None):
    """INSERT/UPDATE/DELETE 쿼리 실행"""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(query, params or ())
            await conn.commit()
            return cursor.rowcount
    finally:
        conn.close()