# 🎉 Posts 파일 업로드 기능 구현 완료

실제 테이블 구조(`files`, `post_attachments`, `TEMP_files`)에 맞춰 **완벽한 파일 업로드 시스템**을 구현했습니다!

---

## 📦 생성된 파일 목록 (총 9개)

### 1️⃣ **Domain Layer**
```
app/domain/entities/file.py                  ← file_entity.py
app/domain/interfaces/file_repository.py     ← file_repository_protocol.py
```

### 2️⃣ **Repository Layer**
```
app/repositories/file_repository.py          ← file_repository.py
app/repositories/post_attachment_repository.py ← post_attachment_repository.py
app/repositories/temp_file_repository.py     ← temp_file_repository.py
```

### 3️⃣ **Service Layer**
```
app/services/file_service.py                 ← file_service.py
```

### 4️⃣ **Schema Layer**
```
app/schemas/file.py                          ← file_schemas.py
```

### 5️⃣ **Controller Layer**
```
app/api/v1/files.py                          ← files_controller.py
```

### 6️⃣ **Dependencies (업데이트)**
```
app/api/dependencies.py                      ← api_dependencies_updated.py
```

---

## 🗄️ 테이블 구조 매핑

### **1. files 테이블**
```sql
CREATE TABLE `files` (
  `id` int NOT NULL AUTO_INCREMENT,
  `original_filename` varchar(255) NOT NULL,      -- 원본 파일명
  `stored_filename` varchar(255) NOT NULL,        -- 저장된 파일명 (고유)
  `file_path` varchar(500) NOT NULL,              -- 파일 경로
  `file_size` bigint NOT NULL,                    -- 파일 크기 (bytes)
  `mime_type` varchar(100) NOT NULL,              -- MIME 타입
  `file_extension` varchar(10) DEFAULT NULL,      -- 확장자
  `uploader_id` int NOT NULL,                     -- 업로더 (users.id FK)
  `upload_ip` varchar(45) DEFAULT NULL,           -- 업로드 IP
  `download_count` int NOT NULL DEFAULT '0',      -- 다운로드 횟수
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_deleted` tinyint(1) DEFAULT '0',            -- Soft Delete
  `is_public` tinyint(1) NOT NULL DEFAULT '1',    -- 공개 여부
  PRIMARY KEY (`id`),
  UNIQUE KEY `stored_filename` (`stored_filename`),
  KEY `idx_uploader` (`uploader_id`),
  CONSTRAINT `files_ibfk_1` FOREIGN KEY (`uploader_id`) REFERENCES `users` (`id`)
)
```

### **2. post_attachments 테이블 (다대다 연결)**
```sql
CREATE TABLE `post_attachments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `post_id` int NOT NULL,                         -- posts.id FK
  `file_id` int NOT NULL,                         -- files.id FK
  `display_order` int DEFAULT '0',                -- 표시 순서
  `is_thumbnail` tinyint(1) DEFAULT '0',          -- 썸네일 여부
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_post_file` (`post_id`,`file_id`),
  CONSTRAINT `post_attachments_ibfk_1` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `post_attachments_ibfk_2` FOREIGN KEY (`file_id`) REFERENCES `files` (`id`) ON DELETE CASCADE
)
```

### **3. TEMP_files 테이블 (임시 파일 관리)**
```sql
CREATE TABLE `TEMP_files` (
  `id` int NOT NULL AUTO_INCREMENT,
  `file_id` int NOT NULL,                         -- files.id FK
  `uploader_id` int NOT NULL,                     -- users.id FK
  `expires_at` timestamp NOT NULL,                -- 만료 시간
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_expires` (`expires_at`),
  CONSTRAINT `temp_files_ibfk_1` FOREIGN KEY (`file_id`) REFERENCES `files` (`id`) ON DELETE CASCADE,
  CONSTRAINT `temp_files_ibfk_2` FOREIGN KEY (`uploader_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
)
```

---

## 🚀 구현된 API 엔드포인트

### **파일 업로드 & 관리**

| Method | Endpoint | 설명 | 인증 | 권한 |
|--------|----------|------|------|------|
| POST | `/api/v1/files/upload` | 파일 업로드 | ✅ | 일반 |
| GET | `/api/v1/files/{file_id}` | 파일 정보 조회 | ❌ | 공개 |
| GET | `/api/v1/files/{file_id}/download` | 파일 다운로드 | ❌ | 공개/권한 |
| DELETE | `/api/v1/files/{file_id}` | 파일 삭제 | ✅ | 본인/관리자 |

### **게시글 첨부파일**

| Method | Endpoint | 설명 | 인증 | 권한 |
|--------|----------|------|------|------|
| POST | `/api/v1/files/posts/{post_id}/attach` | 게시글에 파일 첨부 | ✅ | 일반 |
| GET | `/api/v1/files/posts/{post_id}/attachments` | 게시글 첨부파일 목록 | ❌ | 공개 |

### **임시 파일 정리**

| Method | Endpoint | 설명 | 인증 | 권한 |
|--------|----------|------|------|------|
| POST | `/api/v1/files/cleanup-temp` | 만료된 임시 파일 정리 | ✅ | 관리자 |

---

## ✨ 주요 기능

### 1. **파일 업로드 시스템**
- ✅ 멀티파트 파일 업로드
- ✅ MIME 타입 검증
- ✅ 파일 크기 제한 (이미지: 10MB, 문서: 50MB)
- ✅ 고유 파일명 생성 (UUID + Timestamp)
- ✅ 업로드 IP 기록
- ✅ 공개/비공개 설정

### 2. **임시 파일 시스템**
- ✅ 업로드 시 임시 파일로 등록 (기본 24시간)
- ✅ 게시글 첨부 시 정식 파일로 전환
- ✅ 만료된 임시 파일 자동 정리 (Cron Job 가능)
- ✅ 실제 파일 + DB 레코드 동시 삭제

### 3. **게시글 첨부파일**
- ✅ 다대다 관계 (1개 게시글 : N개 파일)
- ✅ 표시 순서 지정 (display_order)
- ✅ 첫 번째 이미지 자동 썸네일 설정
- ✅ 게시글 삭제 시 연결 자동 삭제 (CASCADE)

### 4. **파일 다운로드**
- ✅ 공개 파일: 누구나 다운로드
- ✅ 비공개 파일: 업로더/관리자만
- ✅ 다운로드 횟수 자동 증가
- ✅ 원본 파일명으로 다운로드

### 5. **파일 삭제**
- ✅ Soft Delete (is_deleted = 1)
- ✅ Hard Delete (실제 파일 삭제)
- ✅ 권한 검증 (본인/관리자)

### 6. **보안 & 검증**
- ✅ 파일 확장자 검증
- ✅ MIME 타입 화이트리스트
- ✅ 파일 크기 제한
- ✅ 접근 권한 확인
- ✅ 삭제된 파일 필터링

---

## 📝 지원 파일 형식

### **이미지**
```
jpg, jpeg, png, gif, webp, bmp, svg
최대 크기: 10MB
```

### **문서**
```
pdf, doc, docx, xls, xlsx, ppt, pptx, txt
최대 크기: 50MB
```

### **압축 파일**
```
zip, rar, 7z
최대 크기: 50MB
```

### **동영상**
```
mp4, avi, mov
최대 크기: 50MB
```

---

## 🔧 설정 (config.py)

`app/core/config.py`에 다음 설정을 추가하세요:

```python
class Settings(BaseSettings):
    # ... 기존 설정 ...
    
    # File Upload
    UPLOAD_DIR: str = "/app/uploads"           # 파일 저장 디렉토리
    MAX_IMAGE_SIZE: int = 10485760             # 10MB (이미지)
    MAX_DOCUMENT_SIZE: int = 52428800          # 50MB (문서)
```

Railway 배포 시 환경 변수:
```bash
UPLOAD_DIR=/app/uploads
MAX_IMAGE_SIZE=10485760
MAX_DOCUMENT_SIZE=52428800
```

---

## 🎯 사용 시나리오

### **시나리오 1: 게시글 작성 + 파일 첨부**

```bash
# 1단계: 파일 업로드 (임시)
POST /api/v1/files/upload
Content-Type: multipart/form-data
Authorization: Bearer {token}

file: [이미지 파일]
is_temp: true

→ Response: { "id": 1, "is_temp": true }

# 2단계: 게시글 작성
POST /api/v1/posts/
Authorization: Bearer {token}

{
  "title": "새 게시글",
  "content": "내용입니다"
}

→ Response: { "id": 100 }

# 3단계: 파일 첨부
POST /api/v1/files/posts/100/attach
Authorization: Bearer {token}

{
  "file_ids": [1]
}

→ Response: { "attached_count": 1 }
```

### **시나리오 2: 첨부파일 조회**

```bash
# 게시글 첨부파일 목록
GET /api/v1/files/posts/100/attachments

→ Response: [
  {
    "id": 1,
    "file": {
      "id": 1,
      "original_filename": "image.jpg",
      "file_size": 123456,
      "is_thumbnail": true
    }
  }
]
```

### **시나리오 3: 파일 다운로드**

```bash
GET /api/v1/files/1/download

→ Response: [파일 다운로드]
```

---

## 🔍 코드 하이라이트

### **1. FileEntity - 비즈니스 메서드**

```python
@dataclass
class FileEntity:
    # ... 필드들 ...
    
    def is_image(self) -> bool:
        """이미지 파일 여부 확인"""
        return self.mime_type.startswith('image/')
    
    def can_access(self, user_id: int, is_admin: bool) -> bool:
        """접근 권한 확인"""
        if self.is_deleted:
            return is_admin
        if self.is_public:
            return True
        return is_admin or self.uploader_id == user_id
    
    def get_human_readable_size(self) -> str:
        """파일 크기를 읽기 쉬운 형식으로 변환"""
        # 123456789 → "117.74 MB"
```

### **2. FileService - 파일 업로드**

```python
async def upload_file(self, file: UploadFile, current_user: UserEntity, ...):
    """
    비즈니스 규칙:
    1. MIME 타입 검증
    2. 파일 크기 검증
    3. 고유 파일명 생성 (UUID + Timestamp)
    4. 디스크에 저장
    5. DB에 메타데이터 저장
    6. 임시 파일 등록 (24시간 후 만료)
    """
    # MIME 타입 검증
    self._validate_mime_type(mime_type)
    
    # 파일 크기 검증
    self._validate_file_size(file_size, is_image)
    
    # 고유 파일명 생성
    stored_filename = self._generate_stored_filename(original_filename)
    # → "20250125_154523_a1b2c3d4e5f6.jpg"
    
    # 파일 저장
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
```

### **3. PostAttachmentRepository - JOIN 쿼리**

```python
async def find_by_post_id_with_files(self, post_id: int):
    """게시글 첨부파일 조회 (파일 정보 포함)"""
    query = """
        SELECT 
            pa.*,
            f.original_filename,
            f.file_size,
            f.mime_type,
            ...
        FROM post_attachments pa
        INNER JOIN files f ON pa.file_id = f.id
        WHERE pa.post_id = %s AND f.is_deleted = 0
        ORDER BY pa.display_order ASC
    """
```

---

## 🛠️ 배치 작업 (Cron Job)

### **만료된 임시 파일 정리**

```python
# 매일 새벽 3시에 실행 (예시)
import schedule
import asyncio

async def cleanup_expired_files():
    file_service = get_file_service()
    deleted_count = await file_service.cleanup_expired_temp_files()
    logger.info(f"Cleaned up {deleted_count} expired temp files")

# 스케줄링
schedule.every().day.at("03:00").do(lambda: asyncio.run(cleanup_expired_files()))
```

또는 관리자가 수동 실행:
```bash
POST /api/v1/files/cleanup-temp
Authorization: Bearer {admin_token}
```

---

## 📂 파일 배치 가이드

### **1. Domain Layer**
```bash
app/domain/entities/file.py              # FileEntity, PostAttachmentEntity, TempFileEntity
app/domain/interfaces/file_repository.py # Repository Protocols
```

### **2. Repository Layer**
```bash
app/repositories/file_repository.py              # FileRepository
app/repositories/post_attachment_repository.py   # PostAttachmentRepository
app/repositories/temp_file_repository.py         # TempFileRepository
```

### **3. Service Layer**
```bash
app/services/file_service.py  # FileService (비즈니스 로직)
```

### **4. Schema Layer**
```bash
app/schemas/file.py  # Pydantic 스키마
```

### **5. Controller Layer**
```bash
app/api/v1/files.py  # Files Router
```

### **6. Dependencies**
```bash
app/api/dependencies.py  # get_file_service() 추가
```

---

## 🔧 Main 애플리케이션에 라우터 등록

`app/main.py`에 다음 코드를 추가하세요:

```python
from app.api.v1 import files

# 라우터 등록
app.include_router(
    files.router,
    prefix="/api/v1",
    tags=["files"]
)
```

---

## 🧪 테스트 예시

### **1. 파일 업로드**

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/files/upload?is_temp=true" \
  -H "Authorization: Bearer {token}" \
  -F "file=@image.jpg"

# Response
{
  "id": 1,
  "original_filename": "image.jpg",
  "stored_filename": "20250125_154523_abc123.jpg",
  "file_size": 123456,
  "mime_type": "image/jpeg",
  "is_temp": true,
  "message": "파일이 성공적으로 업로드되었습니다"
}
```

### **2. 게시글에 파일 첨부**

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/files/posts/1/attach" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "file_ids": [1, 2, 3]
  }'

# Response
{
  "post_id": 1,
  "attached_count": 3,
  "message": "파일이 게시글에 첨부되었습니다"
}
```

### **3. 첨부파일 목록 조회**

```bash
curl "http://127.0.0.1:8000/api/v1/files/posts/1/attachments"

# Response
[
  {
    "id": 1,
    "file_id": 1,
    "is_thumbnail": true,
    "file": {
      "original_filename": "image.jpg",
      "file_size": 123456,
      "mime_type": "image/jpeg"
    }
  }
]
```

### **4. 파일 다운로드**

```bash
curl -O -J "http://127.0.0.1:8000/api/v1/files/1/download"

# 파일 다운로드 (원본 파일명으로 저장됨)
```

---

## ✅ 체크리스트

### **배포 전 확인 사항**

- [ ] 모든 파일을 올바른 위치에 배치
- [ ] `app/main.py`에 라우터 등록
- [ ] `app/api/dependencies.py` 업데이트
- [ ] `app/core/config.py`에 파일 업로드 설정 추가
- [ ] `UPLOAD_DIR` 디렉토리 생성 및 권한 확인
- [ ] Swagger UI에서 API 문서 확인
- [ ] 파일 업로드 테스트
- [ ] 파일 다운로드 테스트
- [ ] 첨부파일 연결 테스트
- [ ] 임시 파일 정리 테스트
- [ ] 권한 검증 테스트

---

## 🎓 학습 포인트

이 구현을 통해 다음을 학습하셨습니다:

1. ✅ **파일 업로드** - UploadFile, aiofiles, 멀티파트
2. ✅ **임시 파일 시스템** - 만료 시간, 자동 정리
3. ✅ **다대다 관계** - post_attachments 중간 테이블
4. ✅ **파일 검증** - MIME 타입, 크기, 확장자
5. ✅ **고유 파일명 생성** - UUID, Timestamp
6. ✅ **파일 다운로드** - FileResponse, 원본 파일명
7. ✅ **권한 관리** - 공개/비공개, 업로더 확인
8. ✅ **CASCADE 삭제** - 게시글 삭제 시 첨부파일 연결 자동 삭제
9. ✅ **썸네일 자동 설정** - 첫 번째 이미지
10. ✅ **표시 순서** - display_order

---

## 🚀 다음 단계

파일 업로드 기능이 완성되었으니, 이제 다음 기능을 추가할 수 있습니다:

1. **이미지 리사이징** (Pillow)
2. **이미지 썸네일 자동 생성**
3. **S3 업로드** (AWS S3, Cloudflare R2)
4. **파일 압축** (gzip)
5. **이미지 워터마크**
6. **바이러스 스캔** (ClamAV)
7. **파일 미리보기** (PDF, 이미지)
8. **드래그 앤 드롭 업로드** (프론트엔드)

---

**파일 업로드 기능 개발 완료! 이제 테스트를 시작하세요! 🎉**