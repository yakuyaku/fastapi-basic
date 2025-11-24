# pytest 설정 및 테스트 가이드

## 📋 파일 구조

```
tests/
├── __init__.py
├── conftest.py          # pytest 설정 및 공통 fixture
├── test_auth.py         # 인증 API 테스트
├── test_users.py        # 사용자 API 테스트
└── README.md           # 이 파일
```

---

## 🚀 빠른 시작

### 1. pytest 설치

```bash
pip install pytest pytest-asyncio httpx
```

### 2. requirements.txt에 추가

```txt
# 기존 패키지들...

# 테스트
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.24.0
```

### 3. 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 파일 실행
pytest tests/test_auth.py

# 특정 클래스 실행
pytest tests/test_auth.py::TestLogin

# 특정 테스트 실행
pytest tests/test_auth.py::TestLogin::test_login_success

# 상세 출력
pytest -v

# 커버리지 포함
pytest --cov=app --cov-report=html
```

---

## 📝 pytest.ini 설정

프로젝트 루트에 `pytest.ini` 파일 생성:

```ini
[pytest]
# 테스트 파일 패턴
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 테스트 디렉토리
testpaths = tests

# 비동기 테스트 지원
asyncio_mode = auto

# 출력 옵션
addopts = 
    -v
    --strict-markers
    --tb=short
    --disable-warnings

# 마커 정의
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    asyncio: Async tests

# 커버리지 설정
[coverage:run]
source = app
omit = 
    */tests/*
    */venv/*
    */__pycache__/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

---

## 🧪 conftest.py 주요 Fixture

### 기본 Fixture

```python
# 동기 클라이언트
def test_example(client):
    response = client.get("/health")
    assert response.status_code == 200

# 비동기 클라이언트
async def test_async_example(async_client):
    response = await async_client.get("/api/users/")
    assert response.status_code == 200

# 인증 헤더
def test_with_auth(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200

# 관리자 헤더
def test_admin_only(client, admin_headers):
    response = client.delete("/api/users/1", headers=admin_headers)
    assert response.status_code in [200, 404]
```

### 데이터 Fixture

```python
# 테스트 사용자 데이터
def test_user_data(test_user_data):
    assert test_user_data["email"] == "test@example.com"

# 실제 DB에 생성된 사용자
async def test_with_real_user(created_test_user):
    assert created_test_user["id"] is not None
```

### 유틸리티 Fixture

```python
# 응답 검증
def test_validation(client, assert_valid_response):
    response = client.get("/health")
    data = assert_valid_response(response, 200)
    assert data["status"] == "healthy"

# 딕셔너리 비교
def test_compare(compare_dict):
    result = {"a": 1, "b": 2, "c": 3}
    expected = {"a": 1, "b": 2}
    assert compare_dict(result, expected, ["a", "b"])

# 성능 측정
def test_performance(benchmark_timer):
    with benchmark_timer("API 호출"):
        # 측정할 코드
        pass
```

---

## 📊 테스트 마커 사용

### 마커 종류

```python
# Unit 테스트
@pytest.mark.unit
def test_unit():
    pass

# Integration 테스트
@pytest.mark.integration
async def test_integration():
    pass

# 느린 테스트
@pytest.mark.slow
def test_slow():
    pass

# 비동기 테스트
@pytest.mark.asyncio
async def test_async():
    pass
```

### 마커로 필터링

```bash
# Unit 테스트만 실행
pytest -m unit

# Integration 테스트만 실행
pytest -m integration

# 느린 테스트 제외
pytest -m "not slow"

# 여러 마커 조합
pytest -m "unit and not slow"
```

---

## 🔍 테스트 작성 가이드

### 1. AAA 패턴 (Arrange-Act-Assert)

```python
def test_create_user(client):
    # Arrange (준비)
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "Test1234!"
    }
    
    # Act (실행)
    response = client.post("/api/users/", json=user_data)
    
    # Assert (검증)
    assert response.status_code == 201
    assert response.json()["email"] == user_data["email"]
```

### 2. Given-When-Then 패턴

```python
def test_login_success(client):
    # Given: 사용자가 생성되어 있음
    user_data = {"email": "test@example.com", "password": "Test1234!"}
    
    # When: 올바른 정보로 로그인
    response = client.post("/api/auth/login", json=user_data)
    
    # Then: 성공 응답과 토큰 반환
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### 3. 경계값 테스트

```python
def test_password_length():
    """비밀번호 길이 검증"""
    # 너무 짧음
    assert validate_password("123") == False
    
    # 최소 길이 (8자)
    assert validate_password("Test1234") == True
    
    # 정상
    assert validate_password("ValidPass123!") == True
```

### 4. 예외 테스트

```python
def test_invalid_email(client):
    """유효하지 않은 이메일"""
    response = client.post("/api/users/", json={
        "email": "invalid-email",
        "username": "test",
        "password": "Test1234!"
    })
    
    assert response.status_code == 422
    assert "email" in response.json()["detail"][0]["loc"]
```

---

## 🎯 테스트 커버리지

### 커버리지 확인

```bash
# 커버리지 측정
pytest --cov=app

# HTML 리포트 생성
pytest --cov=app --cov-report=html

# 특정 모듈만
pytest --cov=app.api --cov-report=term-missing
```

### 커버리지 목표

- **전체:** 80% 이상
- **핵심 로직:** 90% 이상
- **API 엔드포인트:** 100%

---

## 🚦 CI/CD 통합

### GitHub Actions

`.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 📈 테스트 실행 예제

### 기본 실행

```bash
$ pytest
================================ test session starts ================================
platform linux -- Python 3.11.0, pytest-7.4.0
collected 42 items

tests/test_auth.py ........                                                    [ 19%]
tests/test_users.py ..........................                                 [100%]

================================ 42 passed in 2.34s =================================
```

### 상세 출력

```bash
$ pytest -v
================================ test session starts ================================
tests/test_auth.py::TestLogin::test_login_success PASSED                      [  2%]
tests/test_auth.py::TestLogin::test_login_invalid_email PASSED                [  4%]
tests/test_auth.py::TestLogin::test_login_wrong_password PASSED               [  7%]
...
================================ 42 passed in 2.34s =================================
```

### 실패 시

```bash
$ pytest
================================ test session starts ================================
tests/test_auth.py F.......                                                    [ 19%]

==================================== FAILURES =======================================
_________________________ TestLogin.test_login_success _____________________________

    def test_login_success(client):
        response = client.post("/api/auth/login", json={...})
>       assert response.status_code == 200
E       assert 401 == 200

tests/test_auth.py:15: AssertionError
============================== short test summary info ==============================
FAILED tests/test_auth.py::TestLogin::test_login_success - assert 401 == 200
============================ 1 failed, 41 passed in 2.45s ===========================
```

---

## 🐛 디버깅

### 1. pytest 디버그 모드

```bash
# 첫 번째 실패에서 멈춤
pytest -x

# 실패한 테스트만 재실행
pytest --lf

# print 출력 표시
pytest -s

# 상세 로그
pytest -vv --log-cli-level=DEBUG
```

### 2. PDB 사용

```python
def test_debug(client):
    response = client.get("/api/users/")
    
    # 디버거 시작
    import pdb; pdb.set_trace()
    
    assert response.status_code == 200
```

### 3. 로그 확인

```python
def test_with_logging(client, caplog):
    response = client.get("/api/users/")
    
    # 로그 확인
    assert "Getting users" in caplog.text
```

---

## ✅ 테스트 체크리스트

### 필수 테스트

- [ ] 정상 케이스 (Happy Path)
- [ ] 에러 케이스 (Error Cases)
- [ ] 경계값 (Boundary Values)
- [ ] 권한 검증 (Authorization)
- [ ] 인증 검증 (Authentication)
- [ ] 입력 검증 (Input Validation)

### API 테스트

- [ ] 모든 엔드포인트 테스트
- [ ] 모든 HTTP 메서드 테스트
- [ ] 모든 상태 코드 테스트
- [ ] 응답 구조 검증
- [ ] 에러 메시지 검증

---

## 📚 참고 자료

- [pytest 공식 문서](https://docs.pytest.org/)
- [FastAPI 테스팅](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)

---

**마지막 업데이트:** 2025-11-24