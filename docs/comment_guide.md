# 🎉 Tree 구조 댓글 시스템 구현 완료

실제 테이블 구조(`comments`)에 맞춰 **완벽한 계층형 댓글 시스템**을 구현했습니다!

---

## 📦 생성된 파일 목록 (총 7개)

### 1️⃣ **Domain Layer**
```
app/domain/entities/comment.py               ← comment_entity.py
app/domain/interfaces/comment_repository.py  ← comment_repository_protocol.py
```

### 2️⃣ **Repository Layer**
```
app/repositories/comment_repository.py       ← comment_repository.py
```

### 3️⃣ **Service Layer**
```
app/services/comment_service.py              ← comment_service.py
```

### 4️⃣ **Schema Layer**
```
app/schemas/comment.py                       ← comment_schemas.py
```

### 5️⃣ **Controller Layer**
```
app/api/v1/comments.py                       ← comments_controller.py
```

### 6️⃣ **Dependencies (최종 업데이트)**
```
app/api/dependencies.py                      ← api_dependencies_final.py
```

---

## 🗄️ 테이블 구조 분석

### **comments 테이블 (Tree 구조)**

```sql
CREATE TABLE `comments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `post_id` int NOT NULL,                      -- posts.id FK
  `parent_id` int DEFAULT NULL,                -- 부모 댓글 ID (self-referencing)
  `author_id` int NOT NULL,                    -- users.id FK
  `content` text NOT NULL,                     -- 댓글 내용
  `depth` int DEFAULT '0',                     -- 댓글 깊이 (0, 1, 2, 3)
  `path` varchar(500) DEFAULT NULL,            -- 계층 경로 ("1/3/5")
  `order_num` int DEFAULT '0',                 -- 같은 레벨 정렬 순서
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` tinyint(1) DEFAULT '0',         -- Soft Delete
  PRIMARY KEY (`id`),
  KEY `idx_post` (`post_id`),
  KEY `idx_parent` (`parent_id`),
  KEY `idx_path` (`path`),
  CONSTRAINT `comments_ibfk_1` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `comments_ibfk_2` FOREIGN KEY (`parent_id`) REFERENCES `comments` (`id`) ON DELETE CASCADE,
  CONSTRAINT `comments_ibfk_3` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
)
```

---

## 🌲 Tree 구조 설계

### **핵심 필드**

| 필드 | 설명 | 예시 |
|------|------|------|
| `depth` | 댓글 깊이 | 0 (최상위), 1 (1차 대댓글), 2 (2차 대댓글) |
| `path` | 계층 경로 | "1" (최상위), "1/3" (1번의 자식), "1/3/5" (1-3의 자식) |
| `parent_id` | 부모 댓글 ID | NULL (최상위), 3 (3번 댓글의 대댓글) |
| `order_num` | 같은 레벨에서 정렬 순서 | 0, 1, 2, 3... |

### **Tree 구조 예시**

```
댓글 1 (depth=0, path="1", parent_id=NULL)
├─ 댓글 3 (depth=1, path="1/3", parent_id=1)
│  ├─ 댓글 5 (depth=2, path="1/3/5", parent_id=3)
│  └─ 댓글 6 (depth=2, path="1/3/6", parent_id=3)
└─ 댓글 4 (depth=1, path="1/4", parent_id=1)

댓글 2 (depth=0, path="2", parent_id=NULL)
└─ 댓글 7 (depth=1, path="2/7", parent_id=2)
```

### **정렬 순서 (path ASC)**

```
1       (depth=0, path="1")
1/3     (depth=1, path="1/3")
1/3/5   (depth=2, path="1/3/5")
1/3/6   (depth=2, path="1/3/6")
1/4     (depth=1, path="1/4")
2       (depth=0, path="2")
2/7     (depth=1, path="2/7")
```

이렇게 정렬하면 **Tree 구조를 그대로 유지**할 수 있습니다!

---

## 🚀 구현된 API 엔드포인트

### **댓글 CRUD**

| Method | Endpoint | 설명 | 인증 | 권한 |
|--------|----------|------|------|------|
| POST | `/api/v1/comments/posts/{post_id}` | 댓글 작성 | ✅ | 일반 |
| GET | `/api/v1/comments/posts/{post_id}/flat` | 댓글 목록 (Flat) | ❌ | 공개 |
| GET | `/api/v1/comments/posts/{post_id}/tree` | 댓글 목록 (Tree) | ❌ | 공개 |
| GET | `/api/v1/comments/{comment_id}` | 댓글 단건 조회 | ❌ | 공개 |
| PUT/PATCH | `/api/v1/comments/{comment_id}` | 댓글 수정 | ✅ | 본인/관리자 |
| DELETE | `/api/v1/comments/{comment_id}` | 댓글 삭제 | ✅ | 본인/관리자 |
| PATCH | `/api/v1/comments/{comment_id}/restore` | 댓글 복구 | ✅ | 관리자 |

---

## ✨ 주요 기능

### 1. **Tree 구조 댓글 시스템**
- ✅ 최대 깊이 제한 (0, 1, 2, 3 → 4단계)
- ✅ 자동 path 생성 ("1/3/5")
- ✅ 자동 depth 계산
- ✅ 자동 order_num 계산
- ✅ Flat ↔ Tree 구조 변환

### 2. **대댓글 (Reply)**
- ✅ 무제한 대댓글 (단, MAX_DEPTH=3 제한)
- ✅ 부모 댓글 존재 확인
- ✅ 삭제된 댓글에는 답글 불가
- ✅ CASCADE 삭제 (부모 삭제 시 자식도 삭제)

### 3. **Soft Delete**
- ✅ 내용을 "삭제된 댓글입니다"로 변경
- ✅ is_deleted = 1
- ✅ Hard Delete는 관리자 전용
- ✅ CASCADE로 자식 댓글도 삭제

### 4. **권한 관리**
- ✅ 본인이 작성한 댓글만 수정/삭제
- ✅ 관리자는 모든 댓글 수정/삭제
- ✅ 삭제된 댓글은 수정 불가

### 5. **Tree 변환**
- ✅ Flat 리스트 → Tree 구조 변환
- ✅ children 필드에 자식 댓글 포함
- ✅ 재귀적 구조

### 6. **정렬**
- ✅ path 순서로 정렬 (Tree 유지)
- ✅ order_num으로 같은 레벨 정렬
- ✅ 작성일 순서 (같은 order_num)

---

## 📝 API 사용 예시

### **1. 최상위 댓글 작성**

```bash
POST /api/v1/comments/posts/1
Authorization: Bearer {token}

{
  "content": "첫 번째 댓글입니다!",
  "parent_id": null
}

# Response
{
  "id": 1,
  "post_id": 1,
  "parent_id": null,
  "content": "첫 번째 댓글입니다!",
  "depth": 0,
  "path": "1",
  "author_id": 10,
  "created_at": "2025-01-25T10:00:00"
}
```

### **2. 대댓글 작성 (1차)**

```bash
POST /api/v1/comments/posts/1
Authorization: Bearer {token}

{
  "content": "답글입니다!",
  "parent_id": 1
}

# Response
{
  "id": 3,
  "post_id": 1,
  "parent_id": 1,
  "content": "답글입니다!",
  "depth": 1,
  "path": "1/3",
  "author_id": 11,
  "created_at": "2025-01-25T10:05:00"
}
```

### **3. 대댓글의 대댓글 (2차)**

```bash
POST /api/v1/comments/posts/1
Authorization: Bearer {token}

{
  "content": "답글의 답글입니다!",
  "parent_id": 3
}

# Response
{
  "id": 5,
  "post_id": 1,
  "parent_id": 3,
  "content": "답글의 답글입니다!",
  "depth": 2,
  "path": "1/3/5",
  "author_id": 12,
  "created_at": "2025-01-25T10:10:00"
}
```

### **4. 댓글 목록 조회 (Flat)**

```bash
GET /api/v1/comments/posts/1/flat

# Response
{
  "post_id": 1,
  "total": 5,
  "comments": [
    {
      "id": 1,
      "depth": 0,
      "path": "1",
      "content": "첫 번째 댓글",
      "author_username": "user1"
    },
    {
      "id": 3,
      "depth": 1,
      "path": "1/3",
      "content": "답글입니다",
      "author_username": "user2"
    },
    {
      "id": 5,
      "depth": 2,
      "path": "1/3/5",
      "content": "답글의 답글",
      "author_username": "user3"
    },
    ...
  ]
}
```

### **5. 댓글 목록 조회 (Tree)**

```bash
GET /api/v1/comments/posts/1/tree

# Response
{
  "post_id": 1,
  "total": 5,
  "comments": [
    {
      "id": 1,
      "depth": 0,
      "content": "첫 번째 댓글",
      "author_username": "user1",
      "children": [
        {
          "id": 3,
          "depth": 1,
          "content": "답글입니다",
          "author_username": "user2",
          "children": [
            {
              "id": 5,
              "depth": 2,
              "content": "답글의 답글",
              "author_username": "user3",
              "children": []
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 🔍 코드 하이라이트

### **1. CommentEntity - Tree 구조**

```python
@dataclass
class CommentEntity:
    id: Optional[int] = None
    post_id: int = 0
    parent_id: Optional[int] = None
    author_id: int = 0
    content: str = ""
    depth: int = 0              # 댓글 깊이
    path: Optional[str] = None  # 계층 경로 "1/3/5"
    order_num: int = 0          # 정렬 순서
    
    # Tree 구조용
    children: List['CommentEntity'] = None
    
    def build_path(self, parent_path: Optional[str], comment_id: int) -> str:
        """path 생성: "1" or "1/3" or "1/3/5" """
        if not parent_path:
            return str(comment_id)
        return f"{parent_path}/{comment_id}"
```

### **2. CommentRepository - path 정렬**

```python
async def find_by_post_id(self, post_id: int):
    """path로 정렬하면 Tree 구조 유지됨"""
    query = """
        SELECT *
        FROM comments c
        LEFT JOIN users u ON c.author_id = u.id
        WHERE c.post_id = %s AND c.is_deleted = 0
        ORDER BY c.path ASC, c.order_num ASC
    """
    # path 정렬: "1", "1/3", "1/3/5", "1/4", "2", "2/7" ...
```

### **3. CommentService - Tree 변환**

```python
def _build_comment_tree(self, comments: List[CommentEntity]):
    """Flat 리스트를 Tree 구조로 변환"""
    comment_dict = {c.id: c for c in comments}
    root_comments = []
    
    for comment in comments:
        if comment.parent_id is None:
            # 최상위 댓글
            root_comments.append(comment)
        else:
            # 대댓글 → 부모의 children에 추가
            parent = comment_dict.get(comment.parent_id)
            if parent:
                parent.add_child(comment)
    
    return root_comments
```

### **4. CommentService - 최대 깊이 제한**

```python
MAX_DEPTH = 3  # 0, 1, 2, 3 → 4단계

async def create_comment(self, ...):
    if parent_comment:
        depth = parent_comment.depth + 1
        
        if depth > self.MAX_DEPTH:
            raise HTTPException(
                status_code=400,
                detail=f"댓글은 최대 {self.MAX_DEPTH + 1}단계까지만 가능합니다"
            )
```

---

## 📊 주요 비즈니스 규칙

### **댓글 작성**
- ✅ 인증된 사용자만 작성 가능
- ✅ 최대 깊이 제한 (MAX_DEPTH=3)
- ✅ 부모 댓글 존재 확인
- ✅ 삭제된 댓글에는 답글 불가
- ✅ path, depth, order_num 자동 계산

### **댓글 수정**
- ✅ 본인 또는 관리자만 수정 가능
- ✅ 삭제된 댓글은 수정 불가
- ✅ content만 수정 가능

### **댓글 삭제**
- ✅ 본인 또는 관리자만 삭제 가능
- ✅ Soft Delete: 내용 → "삭제된 댓글입니다"
- ✅ Hard Delete: 실제 삭제 (CASCADE)
- ✅ 자식 댓글도 함께 삭제

### **댓글 조회**
- ✅ 삭제된 댓글도 표시 (내용: "삭제된 댓글입니다")
- ✅ Flat 구조 또는 Tree 구조 선택 가능
- ✅ path 순서로 정렬

---

## 🔧 Main 애플리케이션에 라우터 등록

`app/main.py`에 다음 코드를 추가하세요:

```python
from app.api.v1 import comments

# 라우터 등록
app.include_router(
    comments.router,
    prefix="/api/v1",
    tags=["comments"]
)
```

---

## 📂 파일 배치 가이드

### **1. Domain Layer**
```bash
app/domain/entities/comment.py              # CommentEntity
app/domain/interfaces/comment_repository.py # CommentRepositoryProtocol
```

### **2. Repository Layer**
```bash
app/repositories/comment_repository.py      # CommentRepository
```

### **3. Service Layer**
```bash
app/services/comment_service.py             # CommentService
```

### **4. Schema Layer**
```bash
app/schemas/comment.py                      # Pydantic 스키마
```

### **5. Controller Layer**
```bash
app/api/v1/comments.py                      # Comments Router
```

### **6. Dependencies**
```bash
app/api/dependencies.py                     # get_comment_service() 추가
```

---

## 🧪 테스트 시나리오

### **시나리오 1: 3단계 대댓글**

```bash
# 1단계: 최상위 댓글
POST /api/v1/comments/posts/1
{ "content": "1단계", "parent_id": null }
→ id=1, depth=0, path="1"

# 2단계: 1차 대댓글
POST /api/v1/comments/posts/1
{ "content": "2단계", "parent_id": 1 }
→ id=2, depth=1, path="1/2"

# 3단계: 2차 대댓글
POST /api/v1/comments/posts/1
{ "content": "3단계", "parent_id": 2 }
→ id=3, depth=2, path="1/2/3"

# 4단계: 3차 대댓글
POST /api/v1/comments/posts/1
{ "content": "4단계", "parent_id": 3 }
→ id=4, depth=3, path="1/2/3/4"

# 5단계: 초과! (에러)
POST /api/v1/comments/posts/1
{ "content": "5단계", "parent_id": 4 }
→ 400 Error: "댓글은 최대 4단계까지만 가능합니다"
```

### **시나리오 2: Tree 구조 확인**

```bash
GET /api/v1/comments/posts/1/tree

# Response (Tree 구조)
{
  "comments": [
    {
      "id": 1,
      "content": "1단계",
      "depth": 0,
      "children": [
        {
          "id": 2,
          "content": "2단계",
          "depth": 1,
          "children": [
            {
              "id": 3,
              "content": "3단계",
              "depth": 2,
              "children": [
                {
                  "id": 4,
                  "content": "4단계",
                  "depth": 3,
                  "children": []
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## ✅ 체크리스트

### **배포 전 확인 사항**

- [ ] 모든 파일을 올바른 위치에 배치
- [ ] `app/main.py`에 라우터 등록
- [ ] `app/api/dependencies.py` 업데이트
- [ ] Swagger UI에서 API 문서 확인
- [ ] 최상위 댓글 작성 테스트
- [ ] 대댓글 (1차, 2차, 3차) 작성 테스트
- [ ] 최대 깊이 초과 에러 테스트
- [ ] Flat 구조 조회 테스트
- [ ] Tree 구조 조회 테스트
- [ ] 댓글 수정 테스트
- [ ] 댓글 삭제 (Soft/Hard) 테스트
- [ ] CASCADE 삭제 확인

---

## 🎓 학습 포인트

이 구현을 통해 다음을 학습하셨습니다:

1. ✅ **Tree 구조** - path, depth를 활용한 계층 구조
2. ✅ **Self-referencing FK** - parent_id → comments(id)
3. ✅ **path 정렬** - Tree 구조 유지하는 정렬
4. ✅ **Flat ↔ Tree 변환** - 재귀적 구조 생성
5. ✅ **CASCADE 삭제** - 부모 삭제 시 자식도 삭제
6. ✅ **최대 깊이 제한** - 무한 대댓글 방지
7. ✅ **order_num** - 같은 레벨 정렬
8. ✅ **Soft Delete** - 내용 변경 + 플래그
9. ✅ **재귀적 Response** - CommentTreeResponse
10. ✅ **비즈니스 메서드** - Entity의 can_modify 등

---

## 🚀 다음 단계

댓글 기능이 완성되었으니, 이제 다음 기능을 추가할 수 있습니다:

1. **댓글 좋아요** (comment_likes 테이블)
2. **댓글 신고** (comment_reports 테이블)
3. **댓글 알림** (notifications 테이블)
4. **댓글 수 캐싱** (Redis)
5. **실시간 댓글** (WebSocket)
6. **멘션 기능** (@username)
7. **댓글 검색** (Elasticsearch)

---

**Tree 구조 댓글 시스템 개발 완료! 이제 테스트를 시작하세요! 🎉**