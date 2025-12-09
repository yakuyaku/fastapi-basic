# Changelog - Guest User & Password Protection Feature

## 2025-12-09

### 🎉 새로운 기능

#### 게스트 사용자 지원
- ✅ 인증 없이 게시글, 댓글 작성 가능
- ✅ 모든 게스트 콘텐츠는 `guest` 사용자 (ID: 55)로 등록
- ✅ 파일 업로드도 게스트 사용자 허용

#### 비밀번호 보호 시스템
- ✅ 게스트 콘텐츠 생성 시 비밀번호 자동 생성 (8자리)
- ✅ 사용자가 직접 비밀번호 입력 가능 (4-50자)
- ✅ bcrypt 해싱으로 안전하게 저장
- ✅ 수정/삭제 시 비밀번호 검증

---

## 변경된 API 엔드포인트

### Posts API

#### `POST /api/v1/posts/`
- **변경**: 인증 선택적으로 변경
- **추가**: `password` 필드 (optional)
- **추가**: 응답에 `generated_password` 필드

#### `PUT /api/v1/posts/{post_id}`
- **변경**: 인증 선택적으로 변경
- **추가**: 게스트 게시글은 `password` 필드 필수

#### `DELETE /api/v1/posts/{post_id}`
- **변경**: 인증 선택적으로 변경
- **추가**: 게스트 게시글은 `password` 쿼리 파라미터 필수

#### `GET /api/v1/posts/`, `GET /api/v1/posts/{post_id}`
- **변경**: 인증 불필요 (누구나 조회 가능)

### Comments API

#### `POST /api/v1/comments/posts/{post_id}`
- **변경**: 인증 선택적으로 변경
- **추가**: `password` 필드 (optional)
- **추가**: 응답에 `generated_password` 필드

#### `PUT /api/v1/comments/{comment_id}`
- **변경**: 인증 선택적으로 변경
- **추가**: 게스트 댓글은 `password` 필드 필수

#### `DELETE /api/v1/comments/{comment_id}`
- **변경**: 인증 선택적으로 변경
- **추가**: 게스트 댓글은 `password` 쿼리 파라미터 필수

### Files API

#### `POST /api/v1/files/upload`
- **변경**: 인증 선택적으로 변경
- **유지**: 비밀번호 없이 업로드 가능

#### `GET /api/v1/files/{file_id}/download`, `GET /api/v1/files/{file_id}`
- **변경**: 인증 선택적으로 변경
- **유지**: 공개 파일은 누구나 다운로드 가능

---

## 데이터베이스 변경

### 추가된 컬럼

```sql
-- posts 테이블
ALTER TABLE posts
ADD COLUMN password VARCHAR(255) NULL COMMENT '게스트 게시글 비밀번호 (해시)';

-- comments 테이블
ALTER TABLE comments
ADD COLUMN password VARCHAR(255) NULL COMMENT '게스트 댓글 비밀번호 (해시)';

-- files 테이블 (사용 안 함)
ALTER TABLE files
ADD COLUMN password VARCHAR(255) NULL COMMENT '게스트 파일 비밀번호 (해시)';
```

### 마이그레이션 영향
- **기존 데이터**: 영향 없음 (password 필드는 NULL 허용)
- **인증된 사용자 게시글**: password는 NULL로 유지
- **게스트 게시글**: password 필드에 해시 저장

---

## 코드 변경 사항

### 새로 추가된 파일
없음 (기존 파일 수정만)

### 수정된 파일

#### Core
- `app/core/config.py`
  - `GUEST_USER_ID = 55` 추가

- `app/core/security.py`
  - `generate_random_password()` 함수 추가

- `app/core/dependencies.py`
  - `get_optional_user()` 함수 추가

#### Domain Entities
- `app/domain/entities/post.py`
  - `password: Optional[str]` 필드 추가

- `app/domain/entities/comment.py`
  - `password: Optional[str]` 필드 추가

- `app/domain/entities/file.py`
  - `password: Optional[str]` 필드 추가 (미사용)

#### Repositories
- `app/repositories/post_repository.py`
  - `create()` 메서드에 `password` 파라미터 추가
  - 모든 SELECT 쿼리에 `password` 컬럼 추가

- `app/repositories/comment_repository.py`
  - `create()` 메서드에 `password` 파라미터 추가
  - 모든 SELECT 쿼리에 `password` 컬럼 추가

#### Services
- `app/services/post_service.py`
  - `create_post()`: 비밀번호 자동 생성/해싱 로직 추가
  - `update_post()`: 게스트 게시글 비밀번호 검증 추가
  - `delete_post()`: 게스트 게시글 비밀번호 검증 추가

- `app/services/comment_service.py`
  - `create_comment()`: 비밀번호 자동 생성/해싱 로직 추가
  - `update_comment()`: 게스트 댓글 비밀번호 검증 추가
  - `delete_comment()`: 게스트 댓글 비밀번호 검증 추가

- `app/services/file_service.py`
  - 게스트 업로드 지원 (비밀번호 없음)

#### API
- `app/api/dependencies.py`
  - `get_optional_user()` export 추가

- `app/api/v1/posts.py`
  - 모든 엔드포인트를 `get_optional_user()`로 변경
  - POST, PUT에 비밀번호 처리 로직 추가
  - DELETE에 password 쿼리 파라미터 추가

- `app/api/v1/comments.py`
  - 모든 엔드포인트를 `get_optional_user()`로 변경
  - POST, PUT에 비밀번호 처리 로직 추가
  - DELETE에 password 쿼리 파라미터 추가

- `app/api/v1/files.py`
  - GET 엔드포인트를 `get_optional_user()`로 변경

#### Schemas
- `app/schemas/post.py`
  - `PostCreate`: `password` 필드 추가
  - `PostUpdate`: `password` 필드 추가
  - `PostCreateResponse`: `generated_password` 필드 추가

- `app/schemas/comment.py`
  - `CommentCreate`: `password` 필드 추가
  - `CommentUpdate`: `password` 필드 추가
  - `CommentCreateResponse`: `generated_password` 필드 추가

- `app/schemas/file.py`
  - `FileUploadResponse`: `generated_password` 필드 추가 (미사용)

---

## Breaking Changes

### ⚠️ API 변경사항

#### 1. 응답 스키마 변경
**이전:**
```json
{
  "id": 53,
  "title": "게시글"
}
```

**현재:**
```json
{
  "id": 53,
  "title": "게시글",
  "generated_password": "aB3xY7zQ"  // 새로 추가
}
```

**영향**: 프론트엔드에서 `generated_password` 필드 처리 필요

#### 2. 수정 요청 스키마 변경
**게스트 게시글/댓글 수정 시:**
```json
{
  "title": "수정",
  "password": "aB3xY7zQ"  // 필수
}
```

**영향**: 프론트엔드에서 비밀번호 입력 UI 필요

#### 3. 삭제 요청 변경
**게스트 게시글/댓글 삭제 시:**
```
DELETE /api/v1/posts/53?password=aB3xY7zQ  // password 파라미터 필수
```

**영향**: 프론트엔드에서 URL에 password 파라미터 추가 필요

### ✅ 하위 호환성 유지

- **인증된 사용자**: 기존과 동일하게 동작
- **기존 게시글/댓글**: password 필드는 NULL, 수정/삭제 시 토큰만 필요
- **GET 요청**: 변경 없음

---

## 마이그레이션 가이드

### 1. 데이터베이스 마이그레이션
```bash
# MySQL에 접속하여 실행
mysql -u root -p fastapi_db < docs/add_password_column.sql
```

### 2. Guest 사용자 확인
```sql
-- Guest 사용자가 있는지 확인
SELECT id, username FROM users WHERE id = 55;

-- 없으면 생성
INSERT INTO users (id, username, email, password, is_active, is_admin)
VALUES (55, 'guest', 'guest@system.local', 'no-password', 1, 0);
```

### 3. 환경 변수 (선택)
`.env` 파일에 추가 (필요시):
```env
GUEST_USER_ID=55
```

### 4. 서버 재시작
```bash
# 개발 서버
./run_dev.sh

# 또는
uvicorn app.main:app --reload
```

### 5. 프론트엔드 업데이트
- [ ] `generated_password` 필드 처리 로직 추가
- [ ] 비밀번호 저장 (로컬 스토리지)
- [ ] 수정/삭제 시 비밀번호 입력 UI 추가
- [ ] 에러 처리 (401 Unauthorized)

---

## 테스트 결과

### ✅ 통과한 테스트

#### Posts
- [x] 게스트 게시글 생성 (비밀번호 자동 생성)
- [x] 게스트 게시글 생성 (비밀번호 직접 입력)
- [x] 게스트 게시글 수정 (올바른 비밀번호)
- [x] 게스트 게시글 수정 실패 (잘못된 비밀번호)
- [x] 게스트 게시글 삭제 (올바른 비밀번호)
- [x] 인증된 사용자 게시글 수정/삭제 (토큰만)

#### Comments
- [x] 게스트 댓글 생성 (비밀번호 자동 생성)
- [x] 게스트 댓글 수정 (올바른 비밀번호)
- [x] 게스트 댓글 삭제 (올바른 비밀번호)
- [x] 대댓글 작성 (게스트)

#### Files
- [x] 게스트 파일 업로드
- [x] 파일 다운로드 (인증 없음)

---

## 알려진 이슈

### 1. 비밀번호 복구 불가
- **문제**: 비밀번호를 잊으면 복구 방법 없음
- **해결 방법**: 관리자에게 삭제 요청

### 2. 로컬 스토리지 의존
- **문제**: 브라우저 로컬 스토리지 삭제 시 비밀번호 손실
- **권장**: 사용자에게 비밀번호 복사/저장 안내

---

## 향후 계획

### 📌 고려 중인 기능

#### Phase 2 (미정)
- [ ] 이메일 기반 비밀번호 복구
- [ ] 게스트 세션 관리 (쿠키)
- [ ] 비밀번호 변경 기능
- [ ] 게스트 → 회원 전환 기능

#### Phase 3 (미정)
- [ ] 파일에도 비밀번호 적용
- [ ] 비밀번호 정책 강화 (대문자, 특수문자 포함)
- [ ] Rate limiting (게스트 사용자)

---

## 기여자

- **개발**: Claude Code (Anthropic)
- **요청**: yakuyaku
- **날짜**: 2025-12-09

---

## 참고 문서

- [상세 가이드](./guest-user-feature.md)
- [빠른 참조](./api-quick-reference.md)
- [API 문서](http://localhost:8000/docs)
