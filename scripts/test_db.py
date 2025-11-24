import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 변경된 부분: core.database → db.database
from app.db.database import get_db_connection, execute_query, execute_update
import aiomysql


async def create_users_table():
    """users 테이블 생성"""
    create_table_query = """
                         CREATE TABLE IF NOT EXISTS users (
                                                              id INT AUTO_INCREMENT PRIMARY KEY,
                                                              username VARCHAR(50) UNIQUE NOT NULL,
                             email VARCHAR(100) UNIQUE NOT NULL,
                             hashed_password VARCHAR(255) NOT NULL,
                             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                             updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                             ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
                         """

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(create_table_query)
            await conn.commit()
            print("✅ users 테이블 생성 완료!")
    finally:
        conn.close()


async def insert_sample_data():
    """샘플 데이터 입력"""
    check_query = "SELECT COUNT(*) as cnt FROM users"
    conn = await get_db_connection()

    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(check_query)
            result = await cursor.fetchone()

            if result['cnt'] > 0:
                print("⚠️  이미 사용자 데이터가 있습니다.")
                return

            insert_query = """
                           INSERT INTO users (username, email, hashed_password)
                           VALUES (%s, %s, %s) \
                           """

            sample_users = [
                ('jsyang', 'jsyang@example.com', 'hashed_pw_1'),
                ('alice', 'alice@example.com', 'hashed_pw_2'),
                ('bob', 'bob@example.com', 'hashed_pw_3'),
            ]

            for user in sample_users:
                await cursor.execute(insert_query, user)

            await conn.commit()
            print("✅ 샘플 데이터 입력 완료!")

    finally:
        conn.close()


async def get_all_users():
    """모든 사용자 조회"""
    query = """
            SELECT
                id,
                username,
                email,
                created_at,
                updated_at
            FROM users
            ORDER BY id \
            """

    users = await execute_query(query)

    print("\n" + "="*60)
    print("📋 사용자 목록")
    print("="*60)

    if not users:
        print("사용자가 없습니다.")
    else:
        for user in users:
            print(f"ID: {user['id']}")
            print(f"Username: {user['username']}")
            print(f"Email: {user['email']}")
            print(f"Created: {user['created_at']}")
            print(f"Updated: {user['updated_at']}")
            print("-" * 60)

    return users


async def get_user_count():
    """총 사용자 수 조회"""
    query = "SELECT COUNT(*) as total FROM users"
    result = await execute_query(query)
    total = result[0]['total']
    print(f"\n📊 총 사용자 수: {total}명")
    return total


async def main():
    """메인 함수"""
    try:
        print("🚀 데이터베이스 연결 테스트 시작\n")

        #await create_users_table()
        #await insert_sample_data()
        await get_all_users()
        await get_user_count()

        print("\n✅ 모든 테스트 완료!")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())