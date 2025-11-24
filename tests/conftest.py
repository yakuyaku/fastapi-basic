"""
pytest 설정 및 공통 fixture
tests/conftest.py
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient
import aiomysql

from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.db.database import get_db_connection


# ================================================================================
# Event Loop 설정 (비동기 테스트용)
# ================================================================================

@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 생성 (세션 전체에서 공유)"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ================================================================================
# 테스트 클라이언트
# ================================================================================

@pytest.fixture
def client() -> Generator:
    """
    동기 테스트 클라이언트

    사용 예:
        def test_health(client):
            response = client.get("/health")
            assert response.status_code == 200
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """
    비동기 테스트 클라이언트

    사용 예:
        async def test_async_endpoint(async_client):
            response = await async_client.get("/api/users/")
            assert response.status_code == 200
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ================================================================================
# 데이터베이스
# ================================================================================

@pytest.fixture
async def db_connection():
    """
    데이터베이스 연결 (테스트용)

    사용 예:
        async def test_user_query(db_connection):
            async with db_connection.cursor() as cursor:
                await cursor.execute("SELECT * FROM users")
                result = await cursor.fetchone()
    """
    conn = await get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
async def clean_database(db_connection):
    """
    데이터베이스 초기화 (각 테스트 후 정리)

    사용 예:
        async def test_create_user(clean_database):
            # 테스트 코드
            pass  # 테스트 후 자동으로 데이터 정리됨
    """
    # 테스트 전 상태 저장
    yield db_connection

    # 테스트 후 정리 (선택적)
    async with db_connection.cursor() as cursor:
        # 테스트 데이터 삭제 (선택사항)
        await cursor.execute("DELETE FROM users WHERE email LIKE '%test%'")
        await db_connection.commit()


# ================================================================================
# 인증 관련
# ================================================================================

@pytest.fixture
def test_user_data():
    """
    테스트용 사용자 데이터

    사용 예:
        def test_create_user(client, test_user_data):
            response = client.post("/api/users/", json=test_user_data)
    """
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "Test1234!",
        "is_active": True,
        "is_admin": False
    }


@pytest.fixture
def test_admin_data():
    """테스트용 관리자 데이터"""
    return {
        "email": "admin@example.com",
        "username": "adminuser",
        "password": "Admin1234!",
        "is_active": True,
        "is_admin": True
    }


@pytest.fixture
def test_user_token():
    """
    테스트용 일반 사용자 JWT 토큰

    사용 예:
        def test_protected_endpoint(client, test_user_token):
            headers = {"Authorization": f"Bearer {test_user_token}"}
            response = client.get("/api/auth/me", headers=headers)
    """
    token_data = {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com"
    }
    return create_access_token(data=token_data)


@pytest.fixture
def test_admin_token():
    """테스트용 관리자 JWT 토큰"""
    token_data = {
        "user_id": 2,
        "username": "adminuser",
        "email": "admin@example.com"
    }
    return create_access_token(data=token_data)


@pytest.fixture
def auth_headers(test_user_token):
    """
    인증 헤더 (일반 사용자)

    사용 예:
        def test_get_profile(client, auth_headers):
            response = client.get("/api/auth/me", headers=auth_headers)
    """
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def admin_headers(test_admin_token):
    """인증 헤더 (관리자)"""
    return {"Authorization": f"Bearer {test_admin_token}"}


# ================================================================================
# 테스트 사용자 생성 (실제 DB)
# ================================================================================

@pytest.fixture
async def created_test_user(db_connection, test_user_data):
    """
    실제 DB에 테스트 사용자 생성

    사용 예:
        async def test_user_login(client, created_test_user):
            # created_test_user는 실제 DB에 존재하는 사용자
            response = client.post("/api/auth/login", json={
                "email": created_test_user["email"],
                "password": "Test1234!"
            })
    """
    from app.core.security import hash_password

    # 비밀번호 해싱
    password_hash = hash_password(test_user_data["password"])

    # 사용자 생성
    async with db_connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("""
                             INSERT INTO users (email, username, password_hash, is_active, is_admin)
                             VALUES (%s, %s, %s, %s, %s)
                             """, (
                                 test_user_data["email"],
                                 test_user_data["username"],
                                 password_hash,
                                 test_user_data["is_active"],
                                 test_user_data["is_admin"]
                             ))
        await db_connection.commit()

        # 생성된 사용자 조회
        await cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (test_user_data["email"],)
        )
        user = await cursor.fetchone()

    yield user

    # 테스트 후 삭제
    async with db_connection.cursor() as cursor:
        await cursor.execute(
            "DELETE FROM users WHERE email = %s",
            (test_user_data["email"],)
        )
        await db_connection.commit()


@pytest.fixture
async def created_test_admin(db_connection, test_admin_data):
    """실제 DB에 테스트 관리자 생성"""
    from app.core.security import hash_password

    password_hash = hash_password(test_admin_data["password"])

    async with db_connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("""
                             INSERT INTO users (email, username, password_hash, is_active, is_admin)
                             VALUES (%s, %s, %s, %s, %s)
                             """, (
                                 test_admin_data["email"],
                                 test_admin_data["username"],
                                 password_hash,
                                 test_admin_data["is_active"],
                                 test_admin_data["is_admin"]
                             ))
        await db_connection.commit()

        await cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (test_admin_data["email"],)
        )
        admin = await cursor.fetchone()

    yield admin

    async with db_connection.cursor() as cursor:
        await cursor.execute(
            "DELETE FROM users WHERE email = %s",
            (test_admin_data["email"],)
        )
        await db_connection.commit()


# ================================================================================
# Mock 데이터
# ================================================================================

@pytest.fixture
def mock_users_list():
    """테스트용 사용자 목록"""
    return [
        {
            "id": 1,
            "email": "user1@example.com",
            "username": "user1",
            "is_active": True,
            "is_admin": False
        },
        {
            "id": 2,
            "email": "user2@example.com",
            "username": "user2",
            "is_active": True,
            "is_admin": False
        },
        {
            "id": 3,
            "email": "admin@example.com",
            "username": "admin",
            "is_active": True,
            "is_admin": True
        }
    ]


@pytest.fixture
def invalid_token():
    """유효하지 않은 토큰"""
    return "invalid.jwt.token"


@pytest.fixture
def expired_token():
    """만료된 토큰 (테스트용)"""
    from datetime import timedelta
    token_data = {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com"
    }
    # -1일 만료 (이미 만료됨)
    return create_access_token(data=token_data, expires_delta=timedelta(days=-1))


# ================================================================================
# 환경 설정
# ================================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    테스트 환경 설정 (세션 시작 시 자동 실행)
    """
    # 테스트 환경 설정
    import os
    os.environ["ENVIRONMENT"] = "test"

    print("\n" + "="*60)
    print("🧪 테스트 환경 설정 완료")
    print(f"   환경: {settings.ENVIRONMENT}")
    print(f"   DB: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    print("="*60 + "\n")

    yield

    print("\n" + "="*60)
    print("✅ 테스트 완료")
    print("="*60 + "\n")


# ================================================================================
# 유틸리티 함수
# ================================================================================

@pytest.fixture
def assert_valid_response():
    """
    응답 검증 헬퍼

    사용 예:
        def test_create_user(client, assert_valid_response):
            response = client.post("/api/users/", json=data)
            assert_valid_response(response, 201)
    """
    def _assert(response, expected_status: int = 200):
        assert response.status_code == expected_status, \
            f"Expected {expected_status}, got {response.status_code}: {response.text}"
        return response.json()

    return _assert


@pytest.fixture
def compare_dict():
    """
    딕셔너리 비교 헬퍼 (특정 필드만)

    사용 예:
        def test_user_data(compare_dict):
            assert compare_dict(result, expected, ["email", "username"])
    """
    def _compare(actual: dict, expected: dict, keys: list = None):
        if keys is None:
            keys = expected.keys()

        for key in keys:
            assert key in actual, f"Missing key: {key}"
            assert actual[key] == expected[key], \
                f"Key '{key}': expected {expected[key]}, got {actual[key]}"
        return True

    return _compare


# ================================================================================
# 성능 테스트용
# ================================================================================

@pytest.fixture
def benchmark_timer():
    """
    성능 측정 헬퍼

    사용 예:
        def test_performance(benchmark_timer):
            with benchmark_timer("API 호출"):
                # 성능 측정할 코드
                pass
    """
    import time
    from contextlib import contextmanager

    @contextmanager
    def _timer(name: str = "Operation"):
        start = time.time()
        yield
        elapsed = time.time() - start
        print(f"\n⏱️  {name}: {elapsed:.3f}초")

    return _timer


# ================================================================================
# 로깅 설정
# ================================================================================

@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    """테스트용 로깅 설정"""
    import logging

    # 테스트 중 로그 레벨 조정
    logging.getLogger("fastapi_app").setLevel(logging.WARNING)

    yield

    # 원래 레벨로 복구
    logging.getLogger("fastapi_app").setLevel(logging.INFO)


# ================================================================================
# pytest 설정
# ================================================================================

def pytest_configure(config):
    """pytest 설정"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """테스트 항목 수정"""
    for item in items:
        # 비동기 테스트 자동 마킹
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)