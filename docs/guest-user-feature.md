# 게스트 사용자 기능 (Guest User Feature)

## 개요

인증 없이 게시글, 댓글을 작성할 수 있는 게스트 사용자 기능을 지원합니다.
게스트가 작성한 콘텐츠는 비밀번호로 보호되며, 수정/삭제 시 비밀번호 인증이 필요합니다.

## 주요 특징

### 1. 게스트 사용자 식별
- **guest 사용자**: `id=55`, `username='guest'`
- 모든 게스트 콘텐츠는 이 사용자로 등록됩니다
- 설정: `app/core/config.py`의 `GUEST_USER_ID = 55`

### 2. 지원 기능

| 기능 | 게스트 허용 | 비밀번호 필요 |
|------|------------|--------------|
| 게시글 작성 | ✅ | 자동 생성 |
| 게시글 수정 | ✅ | ✅ 필수 |
| 게시글 삭제 | ✅ | ✅ 필수 |
| 댓글 작성 | ✅ | 자동 생성 |
| 댓글 수정 | ✅ | ✅ 필수 |
| 댓글 삭제 | ✅ | ✅ 필수 |
| 파일 업로드 | ✅ | ❌ 불필요 |
| 파일 다운로드 | ✅ | ❌ 불필요 |

### 3. 비밀번호 시스템

#### 생성 시
- **자동 생성**: 비밀번호를 입력하지 않으면 8자리 랜덤 비밀번호 생성
- **직접 입력**: 4-50자 비밀번호 사용 가능
- **저장**: bcrypt 해싱 후 DB 저장
- **반환**: 응답의 `generated_password` 필드로 **1회만** 확인 가능

#### 수정/삭제 시
- **검증**: 비밀번호 일치 확인
- **실패**: 401 Unauthorized 에러 반환

---

## API 사용 가이드

### Posts (게시글)

#### 1. 게시글 작성 (비밀번호 자동 생성)

**Request:**
```bash
POST /api/v1/posts/
Content-Type: application/json

{
  "title": "게스트 게시글",
  "content": "내용입니다"
}
```

**Response:**
```json
{
  "id": 53,
  "title": "게스트 게시글",
  "content": "내용입니다",
  "author_id": 55,
  "view_count": 0,
  "like_count": 0,
  "created_at": "2025-12-09T14:20:53",
  "is_pinned": false,
  "generated_password": "aB3xY7zQ",  // ⚠️ 이 비밀번호를 저장하세요!
  "message": "게시글이 성공적으로 작성되었습니다"
}
```

#### 2. 게시글 작성 (비밀번호 직접 입력)

**Request:**
```bash
POST /api/v1/posts/
Content-Type: application/json

{
  "title": "게스트 게시글",
  "content": "내용입니다",
  "password": "mypassword123"
}
```

**Response:**
```json
{
  "id": 54,
  "generated_password": null,  // 직접 입력한 경우 null
  "message": "게시글이 성공적으로 작성되었습니다"
}
```

#### 3. 게시글 수정 (비밀번호 필수)

**Request:**
```bash
PUT /api/v1/posts/53
Content-Type: application/json

{
  "title": "수정된 제목",
  "content": "수정된 내용",
  "password": "aB3xY7zQ"  // ✅ 필수
}
```

**Success Response:**
```json
{
  "id": 53,
  "title": "수정된 제목",
  "content": "수정된 내용",
  "updated_at": "2025-12-09T15:30:00"
}
```

**Error Response (비밀번호 틀림):**
```json
{
  "detail": "비밀번호가 일치하지 않습니다"
}
```

#### 4. 게시글 삭제 (비밀번호 필수)

**Request:**
```bash
DELETE /api/v1/posts/53?password=aB3xY7zQ
```

**Success Response:**
```json
{
  "id": 53,
  "message": "게시글이 성공적으로 삭제되었습니다"
}
```

---

### Comments (댓글)

#### 1. 댓글 작성 (비밀번호 자동 생성)

**Request:**
```bash
POST /api/v1/comments/posts/1
Content-Type: application/json

{
  "content": "게스트 댓글입니다"
}
```

**Response:**
```json
{
  "id": 10,
  "post_id": 1,
  "content": "게스트 댓글입니다",
  "author_id": 55,
  "depth": 0,
  "created_at": "2025-12-09T14:30:00",
  "generated_password": "xY9zK3mP",  // ⚠️ 저장 필수!
  "message": "댓글이 성공적으로 작성되었습니다"
}
```

#### 2. 댓글 수정 (비밀번호 필수)

**Request:**
```bash
PUT /api/v1/comments/10
Content-Type: application/json

{
  "content": "수정된 댓글",
  "password": "xY9zK3mP"  // ✅ 필수
}
```

#### 3. 댓글 삭제 (비밀번호 필수)

**Request:**
```bash
DELETE /api/v1/comments/10?password=xY9zK3mP
```

---

### Files (파일)

#### 파일 업로드 (비밀번호 불필요)

**Request:**
```bash
POST /api/v1/files/upload
Content-Type: multipart/form-data

file: [binary data]
is_public: true
is_temp: true
```

**Response:**
```json
{
  "id": 1,
  "original_filename": "image.jpg",
  "file_size": 102400,
  "created_at": "2025-12-09T14:30:00",
  "message": "파일이 성공적으로 업로드되었습니다"
}
```

> ⚠️ **참고**: 파일은 비밀번호 없이 게스트 업로드가 가능합니다.
> 단, 삭제는 인증된 사용자만 본인 파일을 삭제할 수 있습니다.

---

## 데이터베이스 변경사항

### 추가된 컬럼

```sql
-- posts 테이블
ALTER TABLE posts ADD COLUMN password VARCHAR(255) NULL
  COMMENT '게스트 게시글 비밀번호 (해시)';

-- comments 테이블
ALTER TABLE comments ADD COLUMN password VARCHAR(255) NULL
  COMMENT '게스트 댓글 비밀번호 (해시)';

-- files 테이블 (사용 안 함)
ALTER TABLE files ADD COLUMN password VARCHAR(255) NULL
  COMMENT '게스트 파일 비밀번호 (해시)';
```

### 데이터 예시

```sql
-- 게스트 게시글
SELECT id, title, author_id, password
FROM posts
WHERE author_id = 55;

-- 결과
| id | title        | author_id | password                                            |
|----|--------------|-----------|-----------------------------------------------------|
| 53 | 게스트 게시글 | 55        | $2b$12$W84QhYDUOxCotjSSfcRMdOzSYrtSFXeWOfMpw/S8igI... |
```

---

## 보안 고려사항

### 1. 비밀번호 저장
- **해싱**: bcrypt (rounds=12)
- **Salt**: 자동 생성
- **평문 비밀번호**: DB에 저장하지 않음

### 2. 비밀번호 전송
- **생성 시**: 응답에 1회만 포함 (이후 복구 불가)
- **수정/삭제 시**:
  - POST/PUT 요청: Body에 포함
  - DELETE 요청: Query parameter로 전송

### 3. 권한 검증 순서
1. **게스트 콘텐츠**: 비밀번호 검증
2. **인증된 사용자**: 본인 확인
3. **관리자**: 모든 권한

---

## 클라이언트 구현 가이드

### 1. 게시글 작성 플로우

```javascript
// 게시글 작성
const response = await fetch('/api/v1/posts/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: '제목',
    content: '내용'
  })
});

const data = await response.json();

// ⚠️ 중요: 비밀번호를 로컬 스토리지에 저장
if (data.generated_password) {
  localStorage.setItem(`post_${data.id}_password`, data.generated_password);

  // 사용자에게 비밀번호 표시
  alert(`게시글이 작성되었습니다!\n비밀번호: ${data.generated_password}\n(수정/삭제 시 필요합니다)`);
}
```

### 2. 게시글 수정 플로우

```javascript
// 로컬 스토리지에서 비밀번호 가져오기
const password = localStorage.getItem(`post_${postId}_password`);

if (!password) {
  const userPassword = prompt('비밀번호를 입력하세요:');
  if (!userPassword) return;
  password = userPassword;
}

// 수정 요청
const response = await fetch(`/api/v1/posts/${postId}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: '수정된 제목',
    content: '수정된 내용',
    password: password  // ✅ 비밀번호 포함
  })
});

if (response.status === 401) {
  alert('비밀번호가 일치하지 않습니다.');
}
```

### 3. 게시글 삭제 플로우

```javascript
// 로컬 스토리지에서 비밀번호 가져오기
const password = localStorage.getItem(`post_${postId}_password`);

if (!password) {
  const userPassword = prompt('비밀번호를 입력하세요:');
  if (!userPassword) return;
  password = userPassword;
}

// 삭제 요청
const response = await fetch(`/api/v1/posts/${postId}?password=${encodeURIComponent(password)}`, {
  method: 'DELETE'
});

if (response.ok) {
  // 로컬 스토리지에서 비밀번호 제거
  localStorage.removeItem(`post_${postId}_password`);
  alert('게시글이 삭제되었습니다.');
}
```

---

## 테스트 시나리오

### 1. 게스트 게시글 생성 및 수정
```bash
# 1. 게시글 생성 (비밀번호 자동 생성)
curl -X POST "http://localhost:8000/api/v1/posts/" \
  -H "Content-Type: application/json" \
  -d '{"title":"테스트","content":"내용"}'

# 응답: { "id": 53, "generated_password": "aB3xY7zQ" }

# 2. 게시글 수정 (비밀번호 사용)
curl -X PUT "http://localhost:8000/api/v1/posts/53" \
  -H "Content-Type: application/json" \
  -d '{"title":"수정","password":"aB3xY7zQ"}'

# 3. 게시글 삭제 (비밀번호 사용)
curl -X DELETE "http://localhost:8000/api/v1/posts/53?password=aB3xY7zQ"
```

### 2. 비밀번호 오류 테스트
```bash
# 잘못된 비밀번호로 수정 시도
curl -X PUT "http://localhost:8000/api/v1/posts/53" \
  -H "Content-Type: application/json" \
  -d '{"title":"수정","password":"wrong"}'

# 응답: 401 Unauthorized
# { "detail": "비밀번호가 일치하지 않습니다" }
```

---

## FAQ

### Q1. 비밀번호를 잊어버렸어요
**A:** 비밀번호 복구 기능은 없습니다. 게스트 게시글은 비밀번호를 잊어버리면 수정/삭제가 불가능합니다.
관리자에게 문의하여 삭제를 요청할 수 있습니다.

### Q2. 인증된 사용자도 비밀번호가 필요한가요?
**A:** 아니요. 인증된 사용자는 토큰으로 본인 확인이 가능하므로 비밀번호가 필요 없습니다.

### Q3. 비밀번호 길이 제한은?
**A:**
- 최소: 4자
- 최대: 50자
- 자동 생성: 8자 (영문 대소문자 + 숫자)

### Q4. 파일은 왜 비밀번호가 없나요?
**A:** 파일은 다운로드 링크 공유를 위해 비밀번호 없이 설계되었습니다.
대신 `is_public` 플래그로 공개/비공개를 제어할 수 있습니다.

### Q5. 게스트 사용자 ID를 변경하려면?
**A:** `app/core/config.py`의 `GUEST_USER_ID` 값을 수정하면 됩니다.
단, 기존 게스트 콘텐츠는 여전히 이전 ID로 저장되어 있으므로 마이그레이션이 필요할 수 있습니다.

---

## 구현 파일 목록

### 변경된 파일
- `app/core/config.py` - GUEST_USER_ID 설정 추가
- `app/core/security.py` - generate_random_password() 추가
- `app/core/dependencies.py` - get_optional_user() 추가
- `app/api/dependencies.py` - get_optional_user() export

### Posts 관련
- `app/domain/entities/post.py` - password 필드 추가
- `app/repositories/post_repository.py` - password 컬럼 처리
- `app/services/post_service.py` - 비밀번호 로직 구현
- `app/api/v1/posts.py` - Optional authentication
- `app/schemas/post.py` - password, generated_password 필드

### Comments 관련
- `app/domain/entities/comment.py` - password 필드 추가
- `app/repositories/comment_repository.py` - password 컬럼 처리
- `app/services/comment_service.py` - 비밀번호 로직 구현
- `app/api/v1/comments.py` - Optional authentication
- `app/schemas/comment.py` - password, generated_password 필드

### Files 관련
- `app/domain/entities/file.py` - password 필드 추가 (미사용)
- `app/services/file_service.py` - 게스트 업로드 지원
- `app/api/v1/files.py` - Optional authentication

---

## 버전 정보

- **구현 날짜**: 2025-12-09
- **API 버전**: v1
- **Python**: 3.11+
- **FastAPI**: 0.104+
- **데이터베이스**: MySQL 8.0+

---

## 관련 문서

- [API 문서](http://localhost:8000/docs)
- [카테고리 API](./categories.md)
- [인증 시스템](../README.md)
