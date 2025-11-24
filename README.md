# FastAPI 사용자 관리 시스템

FastAPI를 사용하여 구축한 사용자 관리 REST API 프로젝트입니다.

## 📋 프로젝트 개요

이 프로젝트는 FastAPI 학습을 위해 단계별로 개발한 사용자 관리 시스템입니다.
Clean Architecture 원칙을 따르며, 실무에서 사용되는 주요 기능들을 구현했습니다.

## 🏗️ 프로젝트 구조

```
jsyang/
├── .env                      # 환경 변수 설정
├── logs/                     # 애플리케이션 로그
│   └── app.log
├── app/
│   ├── api/                  # API 엔드포인트
│   │   ├── __init__.py
│   │   └── users.py          # 사용자 관련 API
│   ├── core/                 # 핵심 설정
│   │   ├── __init__.py
│   │   ├── config.py         # 환경 설정
│   │   ├── logging.py        # 로깅 설정
│   │   └── security.py       # 보안 (비밀번호 해싱)
│   ├── db/                   # 데이터베이스
│   │   ├── __init__.py
│   │   └── database.py       # DB 연결 및 쿼리 함수
│   ├── middleware/           # 미들웨어
│   │   ├── __init__.py
│   │   ├── request_id.py     # Request ID 생성
│   │   └── logging.py        # 요청/응답 로깅
│   ├── schemas/              # Pydantic 스키마
│   │   ├── __init__.py
│   │   └── user.py           # 사용자 스키마
│   ├── scripts/              # 유틸리티 스크립트
│   │   ├── __init__.py
│   │   ├── config_call.py    # 설정 테스트
│   │   └── test_db.py        # DB 연결 테스트
│   └── main.py               # FastAPI 애플리케이션 진입점
├── tests/                    # 테스트 코드
└── venv/                     # 가상환경
```

## 🚀 주요 기능

### 1. 사용자 관리 (CRUD)
- ✅ **사용자 생성** (POST) - 회원가입
- ✅ **사용자 목록 조회** (GET) - 페이징, 검색, 필터링, 정렬
- ✅ **사용자 단건 조회** (GET)
- ✅ **사용자 정보 수정** (PUT/PATCH)
- ✅ **사용자 삭제** (DELETE) - Hard Delete
- ✅ **사용자 비활성화** (DELETE) - Soft Delete
- ✅ **사용자 복구** (PATCH)

### 2. 보안
- ✅ **비밀번호 해싱** (bcrypt)
- ✅ **입력 데이터 검증** (Pydantic)
- ✅ **이메일/사용자명 중복 체크**

### 3. 로깅 & 모니터링
- ✅ **Request ID 추적** - 각 요청마다 고유 UUID 생성
- ✅ **요청/응답 로깅** - 모든 API 호출 기록
- ✅ **처리 시간 측정** - 성능 모니터링
- ✅ **파일 로깅** - Rotating File Handler (10MB, 30개 백업)
- ✅ **콘솔 출력** - 실시간 로그 확인

### 4. API 기능
- ✅ **자동 API 문서** - Swagger UI (`/docs`)
- ✅ **페이징** - page, page_size
- ✅ **검색** - username, email
- ✅ **필터링** - is_active, is_admin
- ✅ **정렬** - 다양한 필드, 오름차순/내림차순

## 🛠️ 기술 스택

- **Python** 3.11
- **FastAPI** - 현대적인 웹 프레임워크
- **aiomysql** - 비동기 MySQL 드라이버
- **Pydantic** - 데이터 검증
- **bcrypt** - 비밀번호 해싱
- **MySQL** - 데이터베이스
- **Uvicorn** - ASGI 서버

## 📦 설치 및 실행

### 1. 가상환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Mac/Linux)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

### 2. 패키지 설치

```bash
pip install fastapi uvicorn aiomysql pydantic-settings python-dotenv bcrypt
```

### 3. 환경 변수 설정

`.env` 파일 생성:

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=fastapi_user
DB_PASSWORD=fastapi_password
DB_NAME=fastapi_db

# Logging
LOG_DIR=./logs
LOG_LEVEL=INFO
LOG_TO_CONSOLE=true
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=30

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload
UPLOAD_DIR=./uploads
MAX_IMAGE_SIZE=10485760
MAX_DOCUMENT_SIZE=52428800

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Application
ENABLE_REQUEST_LOGGING=true
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=60
ENVIRONMENT=development
```

### 4. 데이터베이스 설정

```sql
-- MySQL 접속
mysql -u root -p

-- 데이터베이스 생성
CREATE DATABASE fastapi_db;

-- 사용자 생성 및 권한 부여
CREATE USER 'fastapi_user'@'localhost' IDENTIFIED BY 'fastapi_password';
GRANT ALL PRIVILEGES ON fastapi_db.* TO 'fastapi_user'@'localhost';
FLUSH PRIVILEGES;

-- 사용자 테이블 생성
USE fastapi_db;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    is_admin TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL,
    last_login_at DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5. 애플리케이션 실행

```bash
uvicorn app.main:app --reload
```

서버가 시작되면: `http://127.0.0.1:8000`

## 📚 API 문서

### Swagger UI
`http://127.0.0.1:8000/docs`

### ReDoc
`http://127.0.0.1:8000/redoc`

## 🔌 API 엔드포인트

### 기본 엔드포인트

```
GET  /                    - 루트 (환영 메시지)
GET  /health             - 헬스 체크
```

### 사용자 관리

```
POST   /api/users/                    - 사용자 생성 (회원가입)
GET    /api/users/                    - 사용자 목록 조회 (페이징, 검색, 필터링)
GET    /api/users/{user_id}           - 특정 사용자 조회
PUT    /api/users/{user_id}           - 사용자 정보 전체 수정
PATCH  /api/users/{user_id}           - 사용자 정보 부분 수정
DELETE /api/users/{user_id}           - 사용자 삭제 (Hard Delete)
DELETE /api/users/{user_id}/soft      - 사용자 비활성화 (Soft Delete)
PATCH  /api/users/{user_id}/restore   - 사용자 복구
```

## 💡 사용 예시

### 1. 사용자 생성

```bash
curl -X POST "http://127.0.0.1:8000/api/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123",
    "is_admin": false
  }'
```

### 2. 사용자 목록 조회 (검색 + 페이징)

```bash
curl "http://127.0.0.1:8000/api/users/?search=test&page=1&page_size=10"
```

### 3. 사용자 정보 수정

```bash
curl -X PUT "http://127.0.0.1:8000/api/users/1" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com",
    "username": "newusername"
  }'
```

### 4. 사용자 비활성화 (Soft Delete)

```bash
curl -X DELETE "http://127.0.0.1:8000/api/users/1/soft"
```

### 5. 사용자 복구

```bash
curl -X PATCH "http://127.0.0.1:8000/api/users/1/restore"
```

## 📊 쿼리 파라미터

### 사용자 목록 조회 옵션

| 파라미터 | 타입 | 설명 | 기본값 |
|---------|------|------|--------|
| `page` | int | 페이지 번호 | 1 |
| `page_size` | int | 페이지당 항목 수 (최대 100) | 10 |
| `search` | string | 검색어 (username 또는 email) | - |
| `is_active` | boolean | 활성 상태 필터 | - |
| `is_admin` | boolean | 관리자 필터 | - |
| `sort_by` | string | 정렬 기준 (id, username, email, created_at) | created_at |
| `sort_order` | string | 정렬 순서 (asc, desc) | desc |

## 🔐 보안 기능

### 비밀번호 규칙
- 최소 8자 이상
- 영문자 최소 1개 포함
- 숫자 최소 1개 포함
- bcrypt 해싱 (rounds=12)

### 사용자명 규칙
- 3-50자
- 영문, 숫자, _, - 만 사용 가능

### 이메일 규칙
- 유효한 이메일 형식
- 중복 불가

## 📝 로깅

### 로그 레벨
- **INFO**: 일반 정보
- **DEBUG**: 상세 디버그 정보
- **WARNING**: 경고
- **ERROR**: 에러 (스택 트레이스 포함)

### 로그 형식
```
2025-11-24 10:00:00 - fastapi_app - INFO - [request-id] → GET /api/users/
2025-11-24 10:00:00 - fastapi_app - INFO - [request-id] ← GET /api/users/ - Status: 200 - Duration: 0.045s
```

### 로그 파일 위치
- `logs/app.log` - 모든 로그 기록
- 자동 로테이션: 10MB마다 새 파일 생성
- 최대 30개 백업 파일 유지

## 🧪 테스트

### 데이터베이스 연결 테스트

```bash
python -m app.scripts.test_db
```

### 설정 확인

```bash
python -m app.scripts.config_call
```

## 🎯 개발 원칙

1. **Clean Architecture** - 계층 분리
2. **Type Safety** - Pydantic을 통한 타입 검증
3. **Logging** - 모든 요청/응답 기록
4. **Error Handling** - 명확한 에러 메시지
5. **Security** - 비밀번호 해싱, 입력 검증
6. **RESTful API** - 표준 HTTP 메서드 사용

## 📈 성능 모니터링

- Request ID를 통한 요청 추적
- 처리 시간 측정 (응답 헤더 `X-Process-Time`)
- SQL 쿼리 최적화 (인덱스 활용)

## 🔄 향후 개발 계획

- [ ] JWT 인증/인가
- [ ] 파일 업로드
- [ ] 이메일 인증
- [ ] 비밀번호 재설정
- [ ] API Rate Limiting
- [ ] CORS 설정
- [ ] 단위 테스트 (pytest)
- [ ] Docker 컨테이너화
- [ ] CI/CD 파이프라인

## 🐛 트러블슈팅

### 1. bcrypt 설치 오류
```bash
pip uninstall bcrypt
pip install bcrypt
```

### 2. MySQL 연결 오류
- MySQL 서버가 실행 중인지 확인
- .env 파일의 DB 설정 확인
- 방화벽 설정 확인

### 3. 포트 이미 사용 중
```bash
# 다른 포트로 실행
uvicorn app.main:app --reload --port 8001
```

## 📖 학습 내용

이 프로젝트를 통해 학습한 내용:

1. FastAPI 기본 개념 및 구조
2. 비동기 프로그래밍 (async/await)
3. Pydantic을 통한 데이터 검증
4. MySQL 비동기 쿼리 (aiomysql)
5. 미들웨어 구현
6. 로깅 시스템 구축
7. RESTful API 설계
8. 보안 (비밀번호 해싱)
9. 에러 핸들링
10. API 문서 자동 생성

## 👨‍💻 개발자

**jsyang**

## 📄 라이선스

이 프로젝트는 학습 목적으로 제작되었습니다.

## 🙏 감사의 말

FastAPI 공식 문서와 커뮤니티에 감사드립니다.

---

**마지막 업데이트:** 2025-11-24