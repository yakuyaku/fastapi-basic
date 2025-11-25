# 🎉 Posts 기능 구현 완료

실제 테이블 구조에 맞춰 **Clean Architecture** 원칙에 따라 Posts 기능을 완성했습니다!

## 📦 생성된 파일 목록

### 1️⃣ **Domain Layer** (순수 비즈니스 로직)
```
app/domain/entities/post.py              ← post_entity.py
app/domain/interfaces/post_repository.py ← post_repository_protocol.py
```

### 2️⃣ **Repository Layer** (데이터 액세스)
```
app/repositories/post_repository.py      ← post_repository.py
```

### 3️⃣ **Service Layer** (비즈니스 로직)
```
app/services/post_service.py             ← post_service.py
```

### 4️⃣ **Schema Layer** (Request/Response)
```
app/schemas/post.py                      ← post_schemas.py
```

### 5️⃣ **Controller Layer** (API Endpoints)
```
app/api/v1/posts.py                      ← posts_controller.py
```

### 6️⃣ **Dependencies** (의존성 주입)
```
app/api/dependencies.py                  ← api_dependencies.py (기존 파일 업데이트)
```

---

## 🗄️ 테이블 구조 매핑

```sql
CREATE TABLE `posts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `content` text NOT NULL,
  `author_id` int NOT NULL,              -- users.id FK
  `view_count` int DEFAULT '0',
  `like_count` int NOT NULL DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` tinyint(1) DEFAULT '0',   -- Soft Delete
  `is_pinned` tinyint(1) NOT NULL DEFAULT '0',   -- 고정 게시글
  `is_locked` tinyint(1) NOT NULL DEFAULT '0',   -- 잠금 (수정 불가)
  PRIMARY KEY (`id`),
  KEY `idx_author` (`author_id`),
  CONSTRAINT `posts_ibfk_1` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
)
```

---

## 🚀 구현된 API 엔드포인트

### **게시글 CRUD**

| Method | Endpoint | 설명 | 인증 | 권한 |
|--------|----------|------|------|------|
| POST | `/api/v1/posts/` | 게시글 작성 | ✅ | 일반 |
| GET | `/api/v1/posts/` | 게시글 목록 조회 | ❌ | 공개 |
| GET | `/api/v1/posts/{post_id}` | 게시글 단건 조회 | ❌ | 공개 |
| PUT/PATCH | `/api/v1/posts/{post_id}` | 게시글 수정 | ✅ | 본인/관리자 |
| DELETE | `/api/v1/posts/{post_id}` | 게시글 삭제 | ✅ | 본인/관리자 |

### **관리자 전용 기능**

| Method | Endpoint | 설명 | 인증 | 권한 |
|--------|----------|------|------|------|
| PATCH | `/api/v1/posts/{post_id}/restore` | 삭제된 게시글 복구 | ✅ | 관리자 |
| PATCH | `/api/v1/posts/{post_id}/pin` | 게시글 고정/해제 | ✅ | 관리자 |
| PATCH | `/api/v1/posts/{post_id}/lock` | 게시글 잠금/해제 | ✅ | 관리자 |

### **좋아요 기능**

| Method | Endpoint | 설명 | 인증 | 권한 |
|--------|----------|------|------|------|
| POST | `/api/v1/posts/{post_id}/like` | 좋아요 | ❌ | 공개 |
| DELETE | `/api/v1/posts/{post_id}/like` | 좋아요 취소 | ❌ | 공개 |

---

## ✨ 주요 기능

### 1. **권한 관리**
- ✅ 본인이 작성한 게시글만 수정/삭제 가능
- ✅ 관리자는 모든 게시글 수정/삭제 가능
- ✅ 잠긴 게시글은 관리자만 수정 가능
- ✅ 고정/잠금 설정은 관리자 전용

### 2. **Soft Delete**
- ✅ 기본은 Soft Delete (`is_deleted = 1`)
- ✅ Hard Delete는 관리자 전용
- ✅ 삭제된 게시글 복구 기능

### 3. **조회수 & 좋아요**
- ✅ 조회수 자동 증가 (선택 가능)
- ✅ Race Condition 방지 (DB 레벨 증가)
- ✅ 좋아요/좋아요 취소 기능

### 4. **고정 & 잠금**
- ✅ 고정 게시글 (목록 상단 표시)
- ✅ 잠긴 게시글 (수정 불가)
- ✅ 토글 기능 (ON/OFF)

### 5. **페이징 & 검색**
- ✅ 페이징 (page, page_size)
- ✅ 검색 (제목, 내용)
- ✅ 필터링 (작성자, 고정 여부)
- ✅ 정렬 (생성일, 조회수, 좋아요 수)
- ✅ 고정 게시글 우선 표시

### 6. **작성자 정보 JOIN**
- ✅ 게시글 조회 시 작성자 정보 포함
- ✅ `author_username`, `author_email`

---

## 📂 파일 배치 가이드

### **1. Domain Layer**
```bash
# Entity
app/domain/entities/post.py

# Protocol (Interface)
app/domain/interfaces/post_repository.py
```

### **2. Repository Layer**
```bash
app/repositories/post_repository.py
```

### **3. Service Layer**
```bash
app/services/post_service.py
```

### **4. Schema Layer**
```bash
app/schemas/post.py
```

### **5. Controller Layer**
```bash
app/api/v1/posts.py
```

### **6. Dependencies 업데이트**
```bash
app/api/dependencies.py  # 기존 파일에 추가
```

기존 `app/api/dependencies.py` 파일에 다음 함수들을 추가하세요:
- `get_post_service()`
- `get_current_user()` (UserEntity 변환)
- `get_current_admin_user()` (이미 있다면 생략)

---

## 🔧 Main 애플리케이션에 라우터 등록

`app/main.py`에 다음 코드를 추가하세요:

```python
from app.api.v1 import posts

# 라우터 등록
app.include_router(
    posts.router,
    prefix="/api/v1",
    tags=["posts"]
)
```

---

## 🧪 테스트 방법

### 1. **Swagger UI 접속**
```
http://127.0.0.1:8000/docs
```

### 2. **게시글 작성 테스트**
```bash
# 1. 로그인하여 토큰 발급
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password"
}

# 2. 게시글 작성
POST /api/v1/posts/
Authorization: Bearer {token}
{
  "title": "첫 번째 게시글",
  "content": "안녕하세요!",
  "is_pinned": false
}
```

### 3. **게시글 목록 조회**
```bash
GET /api/v1/posts/?page=1&page_size=10&search=안녕
```

### 4. **게시글 단건 조회**
```bash
GET /api/v1/posts/1
```

### 5. **게시글 수정**
```bash
PATCH /api/v1/posts/1
Authorization: Bearer {token}
{
  "title": "수정된 제목"
}
```

### 6. **좋아요**
```bash
POST /api/v1/posts/1/like
```

### 7. **게시글 고정 (관리자)**
```bash
PATCH /api/v1/posts/1/pin
Authorization: Bearer {admin_token}
```

---

## 📊 쿼리 파라미터

### **게시글 목록 조회 옵션**

| 파라미터 | 타입 | 설명 | 기본값 |
|---------|------|------|--------|
| `page` | int | 페이지 번호 (1부터 시작) | 1 |
| `page_size` | int | 페이지당 항목 수 (최대 100) | 10 |
| `search` | string | 검색어 (제목 또는 내용) | - |
| `author_id` | int | 작성자 ID 필터 | - |
| `is_pinned` | boolean | 고정 게시글 필터 | - |
| `include_deleted` | boolean | 삭제된 게시글 포함 (관리자 전용) | false |
| `sort_by` | string | 정렬 기준 (id, title, created_at, view_count, like_count) | created_at |
| `sort_order` | string | 정렬 순서 (asc, desc) | desc |

---

## 🎯 비즈니스 규칙 요약

### **게시글 작성**
- ✅ 인증된 사용자만 작성 가능
- ✅ 고정 게시글은 관리자만 생성 가능

### **게시글 수정**
- ✅ 본인 또는 관리자만 수정 가능
- ✅ 잠긴 게시글은 관리자만 수정 가능
- ✅ 삭제된 게시글은 수정 불가
- ✅ 고정/잠금 설정은 관리자만 변경 가능

### **게시글 삭제**
- ✅ 본인 또는 관리자만 삭제 가능
- ✅ 기본은 Soft Delete
- ✅ Hard Delete는 관리자 전용

### **게시글 조회**
- ✅ 삭제된 게시글은 관리자만 조회 가능
- ✅ 조회수 자동 증가 (선택 가능)

---

## 🔍 코드 하이라이트

### **PostEntity (Domain)**
```python
@dataclass
class PostEntity:
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    author_id: int = 0
    view_count: int = 0
    like_count: int = 0
    is_deleted: bool = False
    is_pinned: bool = False
    is_locked: bool = False
    
    def can_modify(self, user_id: int, is_admin: bool) -> bool:
        """수정 권한 확인"""
        return is_admin or self.author_id == user_id
```

### **PostRepository (Raw SQL)**
```python
async def find_all(self, skip, limit, search, ...):
    """작성자 정보 JOIN, 고정 게시글 우선 정렬"""
    query = """
        SELECT p.*, u.username as author_username
        FROM posts p
        LEFT JOIN users u ON p.author_id = u.id
        WHERE p.is_deleted = 0
        ORDER BY p.is_pinned DESC, p.created_at DESC
        LIMIT %s OFFSET %s
    """
```

### **PostService (비즈니스 로직)**
```python
async def update_post(self, post_id, post_data, current_user):
    """권한 검증 + 잠금 체크 + 관리자 권한 분리"""
    if not post.can_modify(current_user.id, current_user.is_admin):
        raise HTTPException(status_code=403, ...)
    
    if post.is_locked and not current_user.is_admin:
        raise HTTPException(status_code=403, ...)
```

---

## ✅ 체크리스트

### **배포 전 확인 사항**

- [ ] 모든 파일을 올바른 위치에 배치
- [ ] `app/main.py`에 라우터 등록
- [ ] `app/api/dependencies.py` 업데이트
- [ ] Swagger UI에서 API 문서 확인
- [ ] 각 엔드포인트 테스트
- [ ] 권한 검증 테스트
- [ ] 페이징/검색 테스트
- [ ] Soft Delete 테스트
- [ ] 고정/잠금 기능 테스트

---

## 🎓 학습 포인트

이 구현을 통해 다음을 학습하셨습니다:

1. ✅ **Clean Architecture** - 4계층 구조
2. ✅ **Repository Pattern** - Raw SQL + Entity 변환
3. ✅ **Service Pattern** - 비즈니스 로직 캡슐화
4. ✅ **DIP (의존성 역전)** - Protocol 기반 설계
5. ✅ **권한 관리** - Entity 메서드로 권한 로직
6. ✅ **Soft Delete** - is_deleted 플래그
7. ✅ **JOIN 쿼리** - 작성자 정보 포함
8. ✅ **Race Condition 방지** - DB 레벨 증가
9. ✅ **Pydantic 검증** - @field_validator
10. ✅ **RESTful API** - 적절한 HTTP 메서드/상태 코드

---

## 🚀 다음 단계

이제 다음 기능들을 추가할 수 있습니다:

1. **댓글 시스템** (Comments)
2. **태그 시스템** (Tags)
3. **카테고리** (Categories)
4. **첨부파일** (File Upload)
5. **북마크** (Bookmarks)
6. **알림** (Notifications)

모두 동일한 Clean Architecture 패턴으로 구현하면 됩니다!

---

**개발 완료! 이제 테스트를 시작하세요! 🎉**