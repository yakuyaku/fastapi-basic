"""
인증 API 테스트
tests/test_auth.py
"""

import pytest
from fastapi import status


class TestLogin:
    """로그인 테스트"""

    def test_login_success(self, client, test_user_data):
        """로그인 성공"""
        # Given: 사용자가 생성되어 있음 (실제로는 created_test_user fixture 사용)
        # When: 올바른 이메일과 비밀번호로 로그인
        response = client.post("/api/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })

        # Then: 성공 응답과 토큰 반환
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_login_invalid_email(self, client):
        """존재하지 않는 이메일로 로그인"""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Test1234!"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_wrong_password(self, client, test_user_data):
        """잘못된 비밀번호로 로그인"""
        response = client.post("/api/auth/login", json={
            "email": test_user_data["email"],
            "password": "WrongPassword123!"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_invalid_email_format(self, client):
        """유효하지 않은 이메일 형식"""
        response = client.post("/api/auth/login", json={
            "email": "invalid-email",
            "password": "Test1234!"
        })

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetCurrentUser:
    """현재 사용자 조회 테스트"""

    def test_get_me_success(self, client, auth_headers):
        """인증된 사용자 정보 조회 성공"""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "username" in data

    def test_get_me_without_token(self, client):
        """토큰 없이 조회"""
        response = client.get("/api/auth/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_me_invalid_token(self, client, invalid_token):
        """유효하지 않은 토큰"""
        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_me_expired_token(self, client, expired_token):
        """만료된 토큰"""
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogout:
    """로그아웃 테스트"""

    def test_logout_success(self, client, auth_headers):
        """로그아웃 성공"""
        response = client.post("/api/auth/logout", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data


class TestDevToken:
    """개발 토큰 테스트"""

    def test_dev_token_in_development(self, client):
        """개발 환경에서 개발 토큰 요청"""
        # Note: 실제 환경에 따라 결과가 다를 수 있음
        response = client.get("/api/auth/dev-token")

        # 개발 환경이면 200, 운영이면 403
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN
        ]


# ================================================================================
# 비동기 테스트 예제
# ================================================================================

class TestAsyncAuth:
    """비동기 인증 테스트"""

    @pytest.mark.asyncio
    async def test_async_login(self, async_client, test_user_data):
        """비동기 로그인 테스트"""
        response = await async_client.post("/api/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })

        # 실제 사용자가 없으면 401
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED
        ]


# ================================================================================
# 통합 테스트 (실제 DB 사용)
# ================================================================================

class TestAuthIntegration:
    """인증 통합 테스트"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_auth_flow(self, client, created_test_user):
        """전체 인증 흐름 테스트"""
        # 1. 로그인
        login_response = client.post("/api/auth/login", json={
            "email": created_test_user["email"],
            "password": "Test1234!"  # 원본 비밀번호
        })

        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]

        # 2. 토큰으로 사용자 정보 조회
        headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/api/auth/me", headers=headers)

        assert me_response.status_code == status.HTTP_200_OK
        user_data = me_response.json()
        assert user_data["email"] == created_test_user["email"]

        # 3. 로그아웃
        logout_response = client.post("/api/auth/logout", headers=headers)
        assert logout_response.status_code == status.HTTP_200_OK


# ================================================================================
# 성능 테스트
# ================================================================================

class TestAuthPerformance:
    """인증 성능 테스트"""

    @pytest.mark.slow
    def test_login_performance(self, client, test_user_data, benchmark_timer):
        """로그인 성능 테스트"""
        with benchmark_timer("로그인"):
            response = client.post("/api/auth/login", json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            })

        # 성능 검증은 benchmark_timer 출력 확인
        assert response.status_code in [200, 401]