"""
database.py 함수 테스트
scripts/test_database.py
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import (
    fetch_one,
    fetch_all,
    execute_query,
    execute_many,
    test_connection
)


async def test_all():
    """모든 데이터베이스 함수 테스트"""

    print("=" * 60)
    print("데이터베이스 연결 테스트")
    print("=" * 60)

    # 1. 연결 테스트
    is_connected = await test_connection()
    print(f"✅ 연결 상태: {'성공' if is_connected else '실패'}")

    if not is_connected:
        print("❌ 데이터베이스 연결 실패")
        return

    print("\n" + "=" * 60)
    print("fetch_one 테스트")
    print("=" * 60)

    # 2. fetch_one 테스트
    user = await fetch_one("SELECT * FROM users LIMIT 1")
    if user:
        print(f"✅ 사용자 조회 성공:")
        for key, value in user.items():
            print(f"  - {key}: {value}")
    else:
        print("⚠️  사용자가 없습니다")

    print("\n" + "=" * 60)
    print("fetch_all 테스트")
    print("=" * 60)

    # 3. fetch_all 테스트
    users = await fetch_all("SELECT id, username, email FROM users LIMIT 5")
    print(f"✅ 사용자 목록 조회: {len(users)}명")
    for i, user in enumerate(users, 1):
        print(f"  {i}. {user['username']} ({user['email']})")

    print("\n" + "=" * 60)
    print("execute_query 테스트 (INSERT)")
    print("=" * 60)

    # 4. INSERT 테스트
    try:
        # 테스트 사용자 생성
        from app.core.security import get_password_hash
        test_username = f"test_user_{int(asyncio.get_event_loop().time())}"
        test_email = f"{test_username}@example.com"
        hashed_password = get_password_hash("test123")

        insert_query = """
                       INSERT INTO users (username, email, hashed_password, is_active, is_superuser)
                       VALUES (%s, %s, %s, %s, %s) \
                       """
        user_id = await execute_query(
            insert_query,
            (test_username, test_email, hashed_password, True, False)
        )
        print(f"✅ 사용자 생성 성공 - ID: {user_id}")

        # 생성된 사용자 조회
        created_user = await fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))
        print(f"  - Username: {created_user['username']}")
        print(f"  - Email: {created_user['email']}")

        print("\n" + "=" * 60)
        print("execute_query 테스트 (UPDATE)")
        print("=" * 60)

        # 5. UPDATE 테스트
        update_query = "UPDATE users SET full_name = %s WHERE id = %s"
        rows = await execute_query(update_query, ("Test User", user_id))
        print(f"✅ 사용자 업데이트 성공 - 영향받은 행: {rows}")

        # 업데이트 확인
        updated_user = await fetch_one("SELECT full_name FROM users WHERE id = %s", (user_id,))
        print(f"  - Full Name: {updated_user['full_name']}")

        print("\n" + "=" * 60)
        print("execute_query 테스트 (DELETE)")
        print("=" * 60)

        # 6. DELETE 테스트
        delete_query = "DELETE FROM users WHERE id = %s"
        rows = await execute_query(delete_query, (user_id,))
        print(f"✅ 사용자 삭제 성공 - 영향받은 행: {rows}")

        # 삭제 확인
        deleted_user = await fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))
        print(f"  - 삭제 확인: {'성공' if deleted_user is None else '실패'}")

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

    print("\n" + "=" * 60)
    print("execute_many 테스트")
    print("=" * 60)

    # 7. execute_many 테스트
    try:
        # 여러 사용자 일괄 생성
        test_users = [
            (f"batch_user_1_{int(asyncio.get_event_loop().time())}",
             f"batch1_{int(asyncio.get_event_loop().time())}@example.com",
             get_password_hash("test123"), True, False),
            (f"batch_user_2_{int(asyncio.get_event_loop().time())}",
             f"batch2_{int(asyncio.get_event_loop().time())}@example.com",
             get_password_hash("test123"), True, False),
        ]

        rows = await execute_many(
            "INSERT INTO users (username, email, hashed_password, is_active, is_superuser) VALUES (%s, %s, %s, %s, %s)",
            test_users
        )
        print(f"✅ 배치 삽입 성공 - {rows}명의 사용자 생성")

        # 생성된 사용자들 삭제 (정리)
        await execute_query("DELETE FROM users WHERE username LIKE 'batch_user_%'")
        print(f"✅ 테스트 사용자 정리 완료")

    except Exception as e:
        print(f"❌ 배치 테스트 실패: {e}")

    print("\n" + "=" * 60)
    print("모든 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_all())