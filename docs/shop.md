# 🛍️ 쇼핑몰 Shops CRUD API 구현 완료

## 📦 생성된 파일 (6개)

```
app/domain/entities/shop.py              ← shop_entity.py
app/domain/interfaces/shop_repository.py ← shop_repository_protocol.py
app/repositories/shop_repository.py      ← shop_repository.py
app/services/shop_service.py             ← shop_service.py
app/schemas/shop.py                      ← shop_schemas.py
app/api/v1/shops.py                      ← shops_controller.py
```

## 🚀 API 엔드포인트

| Method | Endpoint | 설명 | 인증 | 권한 |
|--------|----------|------|------|------|
| POST | `/api/v1/shops/` | 상점 생성 | ✅ | 일반 |
| GET | `/api/v1/shops/` | 상점 목록 (필터링, 페이징) | ❌ | 공개 |
| GET | `/api/v1/shops/my` | 내 상점 목록 | ✅ | 일반 |
| GET | `/api/v1/shops/code/{shop_code}` | 상점 코드로 조회 | ❌ | 공개 |
| GET | `/api/v1/shops/{shop_no}` | 상점 단건 조회 | ❌ | 공개 |
| PUT | `/api/v1/shops/{shop_no}` | 상점 수정 | ✅ | 운영자/관리자 |
| DELETE | `/api/v1/shops/{shop_no}` | 상점 삭제 | ✅ | 관리자 |
| PATCH | `/api/v1/shops/{shop_no}/restore` | 상점 복구 | ✅ | 관리자 |
| PATCH | `/api/v1/shops/{shop_no}/status` | 상태 변경 | ✅ | 운영자/관리자 |
| PATCH | `/api/v1/shops/{shop_no}/toggle-display` | 노출 토글 | ✅ | 운영자/관리자 |

## ✨ 주요 기능

### 1. **상점 유형 (ShopType)**
- `MALL`: 종합몰
- `BRAND`: 브랜드샵
- `PERSONAL`: 개인샵

### 2. **상점 상태 (ShopStatus)**
- `ACTIVE`: 활성 (정상 운영)
- `INACTIVE`: 비활성 (운영자가 임시 중단)
- `SUSPENDED`: 정지 (관리자가 강제 정지)

### 3. **권한 관리**
- 상점 생성: 인증된 사용자
- 상점 수정: 운영자 본인 또는 관리자
- 상점 삭제: 관리자만
- 상태 변경:
    - ACTIVE ↔ INACTIVE: 운영자 가능
    - SUSPENDED: 관리자만

### 4. **검증**
- 상점 코드: 영문 소문자, 숫자, 하이픈, 언더스코어 (3-50자)
- 전화번호: 숫자와 하이픈
- 사업자등록번호: 10자리 숫자

### 5. **Soft Delete**
- `deleted_at` 필드 사용
- 복구 기능 제공 (관리자)

## 📝 Dependencies 추가

`app/api/dependencies.py`에 추가:

```python
from app.services.shop_service import ShopService
from app.repositories.shop_repository import ShopRepository

def get_shop_service() -> ShopService:
    shop_repository = ShopRepository()
    return ShopService(shop_repository)
```

## 🔧 Main에 라우터 등록

`app/main.py`:

```python
from app.api.v1 import shops

app.include_router(
    shops.router,
    prefix="/api/v1",
    tags=["shops"]
)
```

## 🧪 테스트 예시

### 상점 생성
```bash
POST /api/v1/shops/
{
  "shop_name": "테스트 쇼핑몰",
  "shop_code": "test-mall",
  "shop_type": "MALL",
  "contact_email": "shop@example.com",
  "contact_phone": "02-1234-5678"
}
```

### 상점 목록 조회
```bash
GET /api/v1/shops/?page=1&page_size=20&shop_type=MALL&shop_status=ACTIVE
```

### 내 상점 조회
```bash
GET /api/v1/shops/my
Authorization: Bearer {token}
```

완료! 🎉