# FastAPI 사용자 관리 시스템

FastAPI를 사용하여 **Clean Architecture** 원칙에 따라 구축한 사용자 관리 REST API 프로젝트입니다.

## 📋 프로젝트 개요

이 프로젝트는 FastAPI 학습을 위해 단계별로 개발한 사용자 관리 시스템입니다.
**Clean Architecture** 원칙을 따르며, Repository/Service 패턴을 적용하여 명확한 책임 분리와 높은 테스트 용이성을 제공합니다.

## 🏛️ Clean Architecture 구조

본 프로젝트는 다음과 같은 4계층 아키텍처를 따릅니다:

```
┌─────────────────────────────────────────┐
│   Controller Layer (API/v1)             │  ← HTTP 요청/응답 처리
├─────────────────────────────────────────┤
│   Service Layer (Business Logic)        │  ← 비즈니스 로직, 권한 검증
├─────────────────────────────────────────┤
│   Repository Layer (Data Access)        │  ← 데이터베이스 작업
├─────────────────────────────────────────┤
│   Domain Layer (Entities & Interfaces)  │  ← 순수 비즈니스 엔티티
└─────────────────────────────────────────┘
```

### 계층별 책임

- **Domain Layer**: 순수 비즈니스 엔티티 및 Repository 인터페이스 (Protocol)
- **Repository Layer**: 데이터베이스 CRUD 작업 (Raw SQL)
- **Service Layer**: 비즈니스 로직, 중복 검사, 권한 검증, 데이터 변환
- **Controller Layer**: HTTP 요청/응답 처리, Service 호출

## 🏗️ 프로젝트 구조

```
jsyang/
├── .env                      # 환경 변수 설정
├── logs/                     # 애플리케이션 로그
│   └── app_YYYY-MM-DD.log
├── app/
│   ├── domain/               # 🆕 도메인 계층
│   │   ├── entities/
│   │   │   └── user.py       # UserEntity (비즈니스 엔티티)
│   │   └── interfaces/
│   │       └── user_repository.py  # Repository Protocol (DIP)
│   │
│   ├── repositories/         # 🆕 저장소 계층
│   │   ├── base.py           # BaseRepository (공통 DB 작업)
│   │   └── user_repository.py  # UserRepository 구현
│   │
│   ├── services/             # 🆕 서비스 계층
│   │   ├── user_service.py   # 사용자 비즈니스 로직
│   │   └── auth_service.py   # 인증 비즈니스 로직
│   │
│   ├── api/                  # 컨트롤러 계층
│   │   ├── v1/               # 🆕 API v1 (Clean Architecture)
│   │   │   ├── users.py      # User 엔드포인트 (thin controllers)
│   │   │   └── auth.py       # Auth 엔드포인트
│   │   └── dependencies.py   # 🆕 의존성 주입 설정
│   │
│   ├── core/                 # 핵심 설정
│   │   ├── config.py         # 환경 설정
│   │   ├── logging.py        # 로깅 설정
│   │   ├── security.py       # 보안 (JWT, 비밀번호 해싱)
│   │   └── dependencies.py   # 인증 의존성
│   │
│   ├── db/                   # 데이터베이스
│   │   └── database.py       # DB 연결 및 쿼리 함수
│   │
│   ├── middleware/           # 미들웨어
│   │   ├── request_id.py     # Request ID 생성
│   │   └── logging.py        # 요청/응답 로깅
│   │
│   ├── schemas/              # Pydantic 스키마
│   │   ├── user.py           # 사용자 Request/Response 스키마
│   │   └── auth.py           # 인증 Request/Response 스키마
│   │
│   └── main.py               # FastAPI 애플리케이션 진입점
│
├── tests/                    # 테스트 코드
│   ├── unit/                 # 단위 테스트
│   │   ├── repositories/     # Repository 테스트
│   │   └── services/         # Service 테스트
│   └── integration/          # 통합 테스트
│
└── venv/                     # 가상환경
```

## 🚀 주요 기능

### 1. 사용자 관리 (CRUD)
- ✅ **사용자 생성** (POST) - 회원가입
- ✅ **사용자 목록 조회** (GET) - 페이징, 검색, 필터링, 정렬
- ✅ **사용자 단건 조회** (GET) - 권한 검증
- ✅ **사용자 정보 수정** (PUT/PATCH) - 권한 검증
- ✅ **사용자 삭제** (DELETE) - Hard Delete (관리자 전용)
- ✅ **사용자 비활성화** (PATCH) - Soft Delete (관리자 전용)
- ✅ **사용자 복구** (PATCH) - 비활성화 취소 (관리자 전용)

### 2. 인증 & 인가 (JWT)
- ✅ **로그인** (POST) - JWT 토큰 발급
- ✅ **로그아웃** (POST) - 클라이언트 측 토큰 삭제
- ✅ **현재 사용자 조회** (GET) - JWT 인증
- ✅ **개발 토큰** (GET) - 개발 환경 전용
- ✅ **역할 기반 접근 제어** (RBAC) - 일반 사용자 / 관리자

### 3. 보안
- ✅ **JWT 인증** (HS256, 30분 만료)
- ✅ **비밀번호 해싱** (bcrypt, 12 rounds)
- ✅ **입력 데이터 검증** (Pydantic)
- ✅ **이메일/사용자명 중복 체크**
- ✅ **권한 검증** (본인 또는 관리자만 접근)

### 4. 로깅 & 모니터링
- ✅ **Request ID 추적** - 각 요청마다 고유 UUID 생성
- ✅ **요청/응답 로깅** - 모든 API 호출 기록
- ✅ **처리 시간 측정** - 성능 모니터링
- ✅ **파일 로깅** - Rotating File Handler (10MB, 30개 백업)
- ✅ **콘솔 출력** - 실시간 로그 확인
- ✅ **구조화된 로깅** - Request ID 기반 추적

### 5. API 기능
- ✅ **자동 API 문서** - Swagger UI (`/docs`)
- ✅ **페이징** - page, page_size
- ✅ **검색** - username, email
- ✅ **필터링** - is_active, is_admin
- ✅ **정렬** - 다양한 필드, 오름차순/내림차순
- ✅ **버전 관리** - API v1 (`/api/v1/`)

## 🛠️ 기술 스택

### Backend
- **Python** 3.11
- **FastAPI** - 현대적인 웹 프레임워크
- **aiomysql** - 비동기 MySQL 드라이버
- **Pydantic** - 데이터 검증 및 스키마
- **Uvicorn** - ASGI 서버

### Security
- **bcrypt** - 비밀번호 해싱
- **python-jose** - JWT 토큰 처리
- **passlib** - 비밀번호 유틸리티

### Database
- **MySQL** 8.0+ - 관계형 데이터베이스

### Development
- **python-dotenv** - 환경 변수 관리
- **pytest** - 테스트 프레임워크

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
pip install -r requirements.txt
```

또는 개별 설치:

```bash
pip install fastapi uvicorn aiomysql pydantic pydantic-settings \
            python-dotenv bcrypt python-jose passlib email-validator
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

# Security (JWT)
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Development Token (optional, for testing)
DEV_ACCESS_TOKEN=your-dev-token

# Logging
LOG_DIR=./logs
LOG_LEVEL=DEBUG
LOG_TO_CONSOLE=true
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=30

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Application
ENVIRONMENT=development
ENABLE_REQUEST_LOGGING=true
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
    last_login_at DATETIME NULL,
    INDEX idx_email (email),
    INDEX idx_username (username),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5. 애플리케이션 실행

```bash
# 개발 모드 (자동 재시작)
uvicorn app.main:app --reload

# 프로덕션 모드
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

서버가 시작되면: `http://127.0.0.1:8000`

## 📚 API 문서

### Swagger UI (대화형 문서)
`http://127.0.0.1:8000/docs`

### ReDoc (읽기 전용 문서)
`http://127.0.0.1:8000/redoc`

## 🔌 API 엔드포인트

### 기본 엔드포인트

```
GET  /                    - 루트 (환영 메시지)
GET  /health             - 헬스 체크
GET  /dev-info           - 개발 환경 정보 (개발 전용)
```

### 인증 (Authentication)

```
POST   /api/auth/login         - 로그인 (JWT 토큰 발급)
GET    /api/auth/me            - 현재 사용자 정보 조회 🔒
POST   /api/auth/logout        - 로그아웃 🔒
GET    /api/auth/dev-token     - 개발 토큰 발급 (개발 전용)
```

🔒 = 인증 필요 (Bearer Token)

### 사용자 관리 (User Management)

```
POST   /api/users/                    - 사용자 생성 (회원가입)
GET    /api/users/                    - 사용자 목록 조회 (페이징, 검색, 필터링) 🔒👑
GET    /api/users/{user_id}           - 특정 사용자 조회 🔒
PUT    /api/users/{user_id}           - 사용자 정보 전체 수정 🔒
PATCH  /api/users/{user_id}           - 사용자 정보 부분 수정 🔒
DELETE /api/users/{user_id}           - 사용자 삭제 (Hard Delete) 🔒👑
PATCH  /api/users/{user_id}/deactivate - 사용자 비활성화 (Soft Delete) 🔒👑
PATCH  /api/users/{user_id}/restore   - 사용자 복구 🔒👑
```

🔒 = 인증 필요 (Bearer Token)
👑 = 관리자 권한 필요

## 💡 사용 예시

### 1. 사용자 생성 (회원가입)

```bash
curl -X POST "http://127.0.0.1:8000/api/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "Test1234",
    "is_admin": false
  }'
```

### 2. 로그인 (JWT 토큰 발급)

```bash
curl -X POST "http://127.0.0.1:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Test1234"
  }'
```

응답:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "testuser",
    "is_admin": false
  }
}
```

### 3. 현재 사용자 정보 조회 (인증 필요)

```bash
TOKEN="your-jwt-token-here"

curl "http://127.0.0.1:8000/api/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. 사용자 목록 조회 (관리자 전용)

```bash
curl "http://127.0.0.1:8000/api/users/?search=test&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

### 5. 사용자 정보 수정 (인증 필요)

```bash
curl -X PATCH "http://127.0.0.1:8000/api/users/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com"
  }'
```

### 6. 개발 토큰 발급 (개발 환경 전용)

```bash
curl "http://127.0.0.1:8000/api/auth/dev-token"
```

## 📊 쿼리 파라미터

### 사용자 목록 조회 옵션

| 파라미터 | 타입 | 설명 | 기본값 |
|---------|------|------|--------|
| `page` | int | 페이지 번호 (1부터 시작) | 1 |
| `page_size` | int | 페이지당 항목 수 (최대 100) | 10 |
| `search` | string | 검색어 (username 또는 email) | - |
| `is_active` | boolean | 활성 상태 필터 (true/false) | - |
| `is_admin` | boolean | 관리자 필터 (true/false) | - |
| `sort_by` | string | 정렬 기준 (id, username, email, created_at) | created_at |
| `sort_order` | string | 정렬 순서 (asc, desc) | desc |

## 🔐 보안 기능

### JWT 인증
- **알고리즘**: HS256
- **만료 시간**: 30분 (설정 가능)
- **토큰 위치**: Authorization 헤더 (`Bearer {token}`)
- **자동 갱신**: 미지원 (재로그인 필요)

### 비밀번호 규칙
- 최소 8자 이상
- 영문자 최소 1개 포함
- 숫자 최소 1개 포함
- bcrypt 해싱 (rounds=12)

### 사용자명 규칙
- 3-50자
- 영문, 숫자, _, - 만 사용 가능
- 중복 불가

### 이메일 규칙
- 유효한 이메일 형식 (RFC 5322)
- 중복 불가

### 권한 검증
- **본인 확인**: 사용자 조회/수정 시 본인 또는 관리자만 접근 가능
- **관리자 전용**: 사용자 목록 조회, 삭제, 비활성화, 복구
- **자기 자신 보호**: 관리자도 자기 자신은 삭제/비활성화 불가

## 📝 로깅

### 로그 레벨
- **DEBUG**: 상세 디버그 정보 (개발 환경)
- **INFO**: 일반 정보 (프로덕션 환경)
- **WARNING**: 경고 (권한 거부, 중복 시도 등)
- **ERROR**: 에러 (스택 트레이스 포함)

### 로그 형식
```
2025-11-25 10:00:00 - fastapi_app - INFO - [request-id] Creating user - username: testuser, email: test@example.com
2025-11-25 10:00:01 - fastapi_app - INFO - [request-id] User created in DB - ID: 1, username: testuser
2025-11-25 10:00:01 - fastapi_app - INFO - [request-id] User created successfully - ID: 1, username: testuser
2025-11-25 10:00:01 - fastapi_app - INFO - [request-id] ← POST /api/users/ - Status: 201 - Duration: 0.350s
```

### 로그 파일 위치
- `logs/app_YYYY-MM-DD.log` - 날짜별 로그 파일
- 자동 로테이션: 10MB마다 새 파일 생성
- 최대 30개 백업 파일 유지

## 🧪 테스트

### 데이터베이스 연결 테스트

```bash
python -m app.scripts.test_db
```

### API 테스트 (Swagger UI 사용)

1. 브라우저에서 `http://127.0.0.1:8000/docs` 접속
2. "Try it out" 버튼 클릭
3. 파라미터 입력 후 "Execute" 실행

## 🎯 아키텍처 원칙

### 1. Clean Architecture
- **계층 분리**: Domain → Repository → Service → Controller
- **의존성 역전 (DIP)**: Service는 Repository 인터페이스(Protocol)에 의존
- **단일 책임 원칙 (SRP)**: 각 계층은 하나의 책임만 가짐

### 2. 설계 패턴
- **Repository Pattern**: 데이터 액세스 추상화
- **Service Pattern**: 비즈니스 로직 캡슐화
- **Dependency Injection**: FastAPI의 Depends를 통한 DI
- **DTO Pattern**: Pydantic 스키마를 통한 데이터 전송 객체

### 3. 코드 품질
- **Type Safety**: Pydantic을 통한 타입 검증
- **Logging**: 모든 요청/응답 및 비즈니스 로직 기록
- **Error Handling**: 명확한 에러 메시지 및 HTTP 상태 코드
- **Security**: 비밀번호 해싱, 입력 검증, JWT 인증
- **RESTful API**: 표준 HTTP 메서드 및 상태 코드 사용

### 4. 테스트 용이성
- **단위 테스트**: Service/Repository 계층을 독립적으로 테스트
- **Mock 가능**: Protocol 기반 의존성으로 쉬운 Mock 주입
- **통합 테스트**: 전체 스택 테스트 가능

## 📈 성능 모니터링

- **Request ID**: UUID 기반 요청 추적 (`X-Request-Id` 헤더)
- **처리 시간**: 각 요청의 처리 시간 로깅
- **SQL 쿼리 최적화**: 인덱스 활용 (email, username, is_active)
- **비동기 처리**: aiomysql을 통한 non-blocking I/O

## 🔄 개발 완료 항목

- ✅ **JWT 인증/인가** - Bearer Token, Role-based access control
- ✅ **Clean Architecture** - 4계층 구조 (Domain, Repository, Service, Controller)
- ✅ **Repository Pattern** - 데이터 액세스 추상화
- ✅ **Service Pattern** - 비즈니스 로직 캡슐화
- ✅ **CORS 설정** - 환경별 설정 가능
- ✅ **환경별 설정** - development, production, test
- ✅ **구조화된 로깅** - Request ID 기반 추적

## 🚀 향후 개발 계획

- [ ] 단위 테스트 (pytest) - Repository, Service 계층
- [ ] 통합 테스트 - API 엔드투엔드 테스트
- [ ] 파일 업로드 - 프로필 이미지, 첨부파일
- [ ] 이메일 인증 - 회원가입 시 이메일 확인
- [ ] 비밀번호 재설정 - 이메일 기반 비밀번호 재설정
- [ ] API Rate Limiting - 요청 빈도 제한
- [ ] Redis 캐싱 - 세션, 토큰 블랙리스트
- [ ] Docker 컨테이너화 - Docker Compose
- [ ] CI/CD 파이프라인 - GitHub Actions
- [ ] API 버전 관리 - v2, v3 등

## 🐛 트러블슈팅

### 1. JWT 토큰 오류

```bash
# 토큰이 만료된 경우
# → 재로그인하여 새 토큰 발급

# 토큰 형식 오류
# → Authorization 헤더 형식 확인: "Bearer {token}"
```

### 2. 권한 거부 (403 Forbidden)

```bash
# 관리자 권한이 필요한 엔드포인트에 일반 사용자로 접근
# → 관리자 계정으로 로그인 필요

# 본인 정보가 아닌 다른 사용자 정보 접근 시도
# → 본인 정보만 조회/수정 가능 (또는 관리자 권한 필요)
```

### 3. bcrypt 설치 오류

```bash
pip uninstall bcrypt
pip install bcrypt
```

### 4. MySQL 연결 오류

- MySQL 서버가 실행 중인지 확인
- .env 파일의 DB 설정 확인
- 방화벽 설정 확인

### 5. 포트 이미 사용 중

```bash
# 다른 포트로 실행
uvicorn app.main:app --reload --port 8001
```

## 📖 학습 내용

이 프로젝트를 통해 학습한 내용:

1. **Clean Architecture** - 4계층 구조 설계 및 구현
2. **Repository Pattern** - 데이터 액세스 추상화
3. **Service Pattern** - 비즈니스 로직 캡슐화
4. **Dependency Injection** - FastAPI Depends를 통한 DI
5. **JWT 인증** - 토큰 기반 인증 및 인가
6. **비동기 프로그래밍** - async/await, aiomysql
7. **Pydantic** - 데이터 검증 및 스키마 정의
8. **RESTful API 설계** - HTTP 메서드, 상태 코드
9. **보안** - 비밀번호 해싱, JWT, 권한 검증
10. **로깅 시스템** - Request ID 기반 추적
11. **에러 핸들링** - HTTPException, 명확한 에러 메시지
12. **API 문서 자동 생성** - Swagger UI, ReDoc

## 📚 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [JWT.io](https://jwt.io/)
- [Pydantic 문서](https://docs.pydantic.dev/)

## 👨‍💻 개발자

**jsyang**

## 📄 라이선스

이 프로젝트는 학습 목적으로 제작되었습니다.

## 🙏 감사의 말

FastAPI 공식 문서, Clean Architecture 커뮤니티, 그리고 오픈소스 컨트리뷰터들에게 감사드립니다.

---

**마지막 업데이트:** 2025-11-25 (Clean Architecture 리팩토링 완료)
