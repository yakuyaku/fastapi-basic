# API Quick Reference - Guest User Features

## 빠른 참조 가이드

### 🔑 비밀번호 규칙

| 항목 | 설명 |
|------|------|
| 자동 생성 | 8자 (영문+숫자) |
| 직접 입력 | 4-50자 |
| 저장 방식 | bcrypt 해싱 |
| 반환 | `generated_password` 필드 (1회만) |

---

## 📝 Posts (게시글) - 비밀번호 보호

### 생성
```bash
POST /api/v1/posts/
{ "title": "제목", "content": "내용" }
# → generated_password: "aB3xY7zQ"
```

### 수정
```bash
PUT /api/v1/posts/53
{ "title": "수정", "password": "aB3xY7zQ" }  # password 필수!
```

### 삭제
```bash
DELETE /api/v1/posts/53?password=aB3xY7zQ  # password 필수!
```

---

## 💬 Comments (댓글) - 비밀번호 보호

### 생성
```bash
POST /api/v1/comments/posts/1
{ "content": "댓글 내용" }
# → generated_password: "xY9zK3mP"
```

### 수정
```bash
PUT /api/v1/comments/10
{ "content": "수정", "password": "xY9zK3mP" }  # password 필수!
```

### 삭제
```bash
DELETE /api/v1/comments/10?password=xY9zK3mP  # password 필수!
```

---

## 📁 Files (파일) - 비밀번호 없음

### 업로드
```bash
POST /api/v1/files/upload
file: [binary]
# 비밀번호 불필요
```

### 다운로드
```bash
GET /api/v1/files/1/download
# 비밀번호 불필요
```

---

## 🚨 에러 코드

| 상태 코드 | 설명 |
|----------|------|
| 401 | 비밀번호가 필요하거나 일치하지 않음 |
| 403 | 권한 없음 (인증된 사용자의 경우) |
| 404 | 리소스를 찾을 수 없음 |

### 에러 응답 예시
```json
{
  "detail": "게스트 게시글 수정을 위해서는 비밀번호가 필요합니다"
}
```

```json
{
  "detail": "비밀번호가 일치하지 않습니다"
}
```

---

## 🔐 인증 방식 비교

| 사용자 타입 | 인증 방법 | 수정/삭제 |
|------------|----------|----------|
| 게스트 | 비밀번호 | 비밀번호 필수 |
| 인증 사용자 | Bearer Token | 토큰만 필요 |
| 관리자 | Bearer Token | 모든 콘텐츠 가능 |

---

## 💡 프론트엔드 체크리스트

### ✅ 게시글/댓글 작성 시
- [ ] `generated_password`를 로컬 스토리지에 저장
- [ ] 사용자에게 비밀번호 표시 (복사 가능하게)
- [ ] 비밀번호 저장 안내 메시지

### ✅ 게시글/댓글 수정 시
- [ ] 로컬 스토리지에서 비밀번호 조회
- [ ] 없으면 사용자에게 입력 요청
- [ ] 비밀번호를 body에 포함

### ✅ 게시글/댓글 삭제 시
- [ ] 로컬 스토리지에서 비밀번호 조회
- [ ] 없으면 사용자에게 입력 요청
- [ ] 비밀번호를 query parameter로 전달
- [ ] 성공 시 로컬 스토리지에서 비밀번호 제거

---

## 🧪 테스트 명령어

### 전체 플로우 테스트
```bash
# 1. 생성
curl -X POST "http://localhost:8000/api/v1/posts/" \
  -H "Content-Type: application/json" \
  -d '{"title":"테스트","content":"내용"}'

# 2. 수정 (비밀번호 사용)
curl -X PUT "http://localhost:8000/api/v1/posts/53" \
  -H "Content-Type: application/json" \
  -d '{"title":"수정","password":"aB3xY7zQ"}'

# 3. 삭제 (비밀번호 사용)
curl -X DELETE "http://localhost:8000/api/v1/posts/53?password=aB3xY7zQ"
```

### 에러 케이스 테스트
```bash
# 비밀번호 없이 수정 시도 → 401
curl -X PUT "http://localhost:8000/api/v1/posts/53" \
  -H "Content-Type: application/json" \
  -d '{"title":"수정"}'

# 잘못된 비밀번호 → 401
curl -X PUT "http://localhost:8000/api/v1/posts/53" \
  -H "Content-Type: application/json" \
  -d '{"title":"수정","password":"wrong"}'
```

---

## 📊 데이터베이스

### Guest User
```sql
-- Guest 사용자 확인
SELECT id, username, email FROM users WHERE id = 55;
```

### Guest 콘텐츠 조회
```sql
-- 게스트 게시글 목록
SELECT id, title, author_id, password IS NOT NULL as has_password
FROM posts
WHERE author_id = 55;

-- 게스트 댓글 목록
SELECT id, content, author_id, password IS NOT NULL as has_password
FROM comments
WHERE author_id = 55;
```

---

## 📌 중요 참고사항

1. **비밀번호는 1회만 확인 가능**: 응답의 `generated_password` 필드
2. **복구 불가**: 비밀번호를 잊으면 수정/삭제 불가
3. **관리자 권한**: 관리자는 비밀번호 없이 모든 콘텐츠 수정/삭제 가능
4. **파일 예외**: 파일은 비밀번호 없이 업로드/다운로드 가능

---

## 🔗 관련 링크

- [상세 문서](./guest-user-feature.md)
- [Swagger UI](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)
