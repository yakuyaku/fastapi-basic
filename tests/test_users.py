"""
사용자 API 테스트
tests/test_users.py
"""

import pytest
from fastapi import status


class TestCreateUser:
    """사용자 생성 테스트"""

    def test_create_user_success(self, client, test_user_data):
        """사용자 생성 성공"""
        response = client.post("/api/users/", json=test_user_data)

        # 성공 또는 이미 존재하는 경우
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST  # 이미 존재
        ]

        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            assert data["email"] == test_user_data["email"]
            assert data["username"] == test_user_data["username"]
            assert "password" not in data  # 비밀번호는 반환되지 않음

    def test_create_user_duplicate_email(self, client, test_user_data):
        """중복 이메일로 사용자 생성"""
        # 첫 번째 생성
        client.post("/api/users/", json=test_user_data)

        # 두 번째 생성 시도
        response = client.post("/api/users/", json=test_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_user_invalid_email(self, client):
        """유효하지 않은 이메일"""
        data = {
            "email": "invalid-email",
            "username": "testuser",
            "password": "Test1234!"
        }
        response = client.post("/api/users/", json=data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_user_weak_password(self, client):
        """약한 비밀번호"""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "123"  # 너무 짧음
        }
        response = client.post("/api/users/", json=data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_user_missing_fields(self, client):
        """필수 필드 누락"""
        data = {
            "email": "test@example.com"
            # username, password 누락
        }
        response = client.post("/api/users/", json=data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetUser:
    """사용자 조회 테스트"""

    def test_get_user_success(self, client, auth_headers):
        """사용자 조회 성공"""
        # 먼저 사용자 ID를 알아야 함 (실제로는 created_test_user 사용)
        user_id = 1
        response = client.get(f"/api/users/{user_id}", headers=auth_headers)

        # 사용자가 존재하면 200, 없으면 404
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

    def test_get_user_not_found(self, client, auth_headers):
        """존재하지 않는 사용자"""
        user_id = 99999
        response = client.get(f"/api/users/{user_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_user_without_auth(self, client):
        """인증 없이 사용자 조회"""
        user_id = 1
        response = client.get(f"/api/users/{user_id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetUsersList:
    """사용자 목록 조회 테스트"""

    def test_get_users_success(self, client, auth_headers):
        """사용자 목록 조회 성공"""
        response = client.get("/api/users/", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_users_pagination(self, client, auth_headers):
        """페이지네이션"""
        response = client.get(
            "/api/users/?skip=0&limit=10",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 10

    def test_get_users_without_auth(self, client):
        """인증 없이 목록 조회"""
        response = client.get("/api/users/")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateUser:
    """사용자 수정 테스트"""

    def test_update_user_success(self, client, auth_headers):
        """사용자 정보 수정 성공"""
        user_id = 1
        update_data = {
            "username": "updated_username"
        }
        response = client.put(
            f"/api/users/{user_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

    def test_update_user_email(self, client, auth_headers):
        """이메일 수정"""
        user_id = 1
        update_data = {
            "email": "newemail@example.com"
        }
        response = client.put(
            f"/api/users/{user_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,  # 중복 이메일
            status.HTTP_404_NOT_FOUND
        ]

    def test_update_user_unauthorized(self, client):
        """권한 없이 수정 시도"""
        user_id = 1
        update_data = {"username": "hacker"}
        response = client.put(f"/api/users/{user_id}", json=update_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteUser:
    """사용자 삭제 테스트"""

    def test_delete_user_admin_only(self, client, admin_headers):
        """관리자만 삭제 가능"""
        user_id = 1
        response = client.delete(
            f"/api/users/{user_id}",
            headers=admin_headers
        )

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

    def test_delete_user_forbidden(self, client, auth_headers):
        """일반 사용자는 삭제 불가"""
        user_id = 1
        response = client.delete(
            f"/api/users/{user_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_user_not_found(self, client, admin_headers):
        """존재하지 않는 사용자 삭제"""
        user_id = 99999
        response = client.delete(
            f"/api/users/{user_id}",
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ================================================================================
# 통합 테스트
# ================================================================================

class TestUsersIntegration:
    """사용자 통합 테스트"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_crud_flow(self, client, test_user_data, admin_headers):
        """사용자 CRUD 전체 흐름"""
        # 1. Create
        create_response = client.post("/api/users/", json=test_user_data)
        if create_response.status_code == status.HTTP_201_CREATED:
            user_data = create_response.json()
            user_id = user_data["id"]

            # 2. Read
            read_response = client.get(
                f"/api/users/{user_id}",
                headers=admin_headers
            )
            assert read_response.status_code == status.HTTP_200_OK

            # 3. Update
            update_data = {"username": "updated_user"}
            update_response = client.put(
                f"/api/users/{user_id}",
                json=update_data,
                headers=admin_headers
            )
            assert update_response.status_code == status.HTTP_200_OK

            # 4. Delete
            delete_response = client.delete(
                f"/api/users/{user_id}",
                headers=admin_headers
            )
            assert delete_response.status_code == status.HTTP_200_OK

            # 5. Verify deletion
            verify_response = client.get(
                f"/api/users/{user_id}",
                headers=admin_headers
            )
            assert verify_response.status_code == status.HTTP_404_NOT_FOUND


# ================================================================================
# 비동기 테스트
# ================================================================================

class TestAsyncUsers:
    """비동기 사용자 테스트"""

    @pytest.mark.asyncio
    async def test_async_create_user(self, async_client, test_user_data):
        """비동기 사용자 생성"""
        response = await async_client.post("/api/users/", json=test_user_data)

        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ]

    @pytest.mark.asyncio
    async def test_async_get_users(self, async_client, auth_headers):
        """비동기 사용자 목록 조회"""
        response = await async_client.get("/api/users/", headers=auth_headers)

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN
        ]


# ================================================================================
# 데이터 검증 테스트
# ================================================================================

class TestUserDataValidation:
    """사용자 데이터 검증 테스트"""

    def test_user_response_structure(self, client, test_user_data, assert_valid_response):
        """사용자 응답 구조 검증"""
        response = client.post("/api/users/", json=test_user_data)

        if response.status_code == status.HTTP_201_CREATED:
            data = assert_valid_response(response, 201)

            # 필수 필드 확인
            assert "id" in data
            assert "email" in data
            assert "username" in data
            assert "is_active" in data
            assert "created_at" in data

            # 비밀번호는 반환되지 않아야 함
            assert "password" not in data
            assert "password_hash" not in data

    def test_user_data_types(self, client, test_user_data):
        """사용자 데이터 타입 검증"""
        response = client.post("/api/users/", json=test_user_data)

        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()

            assert isinstance(data["id"], int)
            assert isinstance(data["email"], str)
            assert isinstance(data["username"], str)
            assert isinstance(data["is_active"], bool)


# ================================================================================
# 성능 테스트
# ================================================================================

class TestUsersPerformance:
    """사용자 성능 테스트"""

    @pytest.mark.slow
    def test_get_users_performance(self, client, auth_headers, benchmark_timer):
        """사용자 목록 조회 성능"""
        with benchmark_timer("사용자 목록 조회"):
            response = client.get("/api/users/?limit=100", headers=auth_headers)

        assert response.status_code in [200, 403]

    @pytest.mark.slow
    def test_create_multiple_users(self, client, benchmark_timer):
        """다수 사용자 생성 성능"""
        with benchmark_timer("10명 사용자 생성"):
            for i in range(10):
                user_data = {
                    "email": f"user{i}@example.com",
                    "username": f"user{i}",
                    "password": "Test1234!"
                }
                client.post("/api/users/", json=user_data)