# 🗂️ 계층형 카테고리 CRUD API 구현 완료

## 📦 생성된 파일 (6개)

```
app/domain/entities/category.py              ← category_entity.py
app/domain/interfaces/category_repository.py ← category_repository_protocol.py
app/repositories/category_repository.py      ← category_repository.py
app/services/category_service.py             ← category_service.py
app/schemas/category.py                      ← category_schemas.py
app/api/v1/categories.py                     ← categories_controller.py
```

## 🎯 핵심 기능

### **1. 계층형 구조 (Path 기반)**
- **최대 4단계**: 대분류(1) → 중분류(2) → 소분류(3) → 세분류(4)
- **category_path**: "1/27/105/" 형태로 계층 관계 저장
- **고성능 조회**: Path LIKE 검색으로 하위 카테고리 일괄 조회

### **2. 멀티샵 지원**
- 복합키: (shop_no, category_no)
- 상점별로 독립적인 카테고리 트리 관리

### **3. 자동 계산 필드**
- `category_depth`: 부모의 depth + 1
- `category_path`: 부모 path + 자신의 ID
- `full_category_name`: "의류 > 하의 > 청바지"

### **4. SEO 최적화**
- `category_code`: URL 친화적 코드
- `meta_keywords`: 검색 키워드
- `hash_tags`: JSON 배열

### **5. 비정규화 최적화**
- `product_count`: 상품 수 (배치 업데이트)

---

## 🚀 API 엔드포인트 (15개)

### **생성/수정/삭제**
| Method | Endpoint | 설명 | 인증 | 권한 |
|--------|----------|------|------|------|
| POST | `/api/v1/categories/shops/{shop_no}` | 카테고리 생성 | ✅ | 일반 |
| PUT | `/api/v1/categories/shops/{shop_no}/{category_no}` | 카테고리 수정 | ✅ | 일반 |
| DELETE | `/api/v1/categories/shops/{shop_no}/{category_no}` | 카테고리 삭제 | ✅ | 관리자 |
| PATCH | `/api/v1/categories/shops/{shop_no}/{category_no}/restore` | 복구 | ✅ | 관리자 |
| PATCH | `/api/v1/categories/shops/{shop_no}/{category_no}/toggle-display` | 노출 토글 | ✅ | 일반 |

### **조회**
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/categories/shops/{shop_no}/roots` | 최상위 카테고리 목록 |
| GET | `/api/v1/categories/shops/{shop_no}/tree` | Tree 구조 조회 (재귀) |
| GET | `/api/v1/categories/shops/{shop_no}/depth/{depth}` | 특정 깊이 카테고리 |
| GET | `/api/v1/categories/shops/{shop_no}/search` | 검색 (키워드) |
| GET | `/api/v1/categories/shops/{shop_no}/code/{code}` | 코드로 조회 |
| GET | `/api/v1/categories/shops/{shop_no}/{category_no}` | 단건 조회 |
| GET | `/api/v1/categories/shops/{shop_no}/{category_no}/children` | 직속 자식 목록 |
| GET | `/api/v1/categories/shops/{shop_no}/{category_no}/descendants` | 하위 전체 조회 |
| GET | `/api/v1/categories/shops/{shop_no}/{category_no}/breadcrumb` | Breadcrumb |

---

## 📊 계층 구조 예시

### **Path 기반 저장**

| category_no | parent_category_no | category_depth | category_path | category_name | full_category_name |
|-------------|-------------------|----------------|---------------|---------------|-------------------|
| 1 | NULL | 1 | `1/` | 의류 | 의류 |
| 27 | 1 | 2 | `1/27/` | 하의 | 의류 > 하의 |
| 105 | 27 | 3 | `1/27/105/` | 청바지 | 의류 > 하의 > 청바지 |
| 2 | NULL | 1 | `2/` | 전자기기 | 전자기기 |
| 50 | 2 | 2 | `2/50/` | 스마트폰 | 전자기기 > 스마트폰 |

### **조회 성능 최적화**

```sql
-- "의류" 하위 전체 조회 (category_no=1, path="1/")
SELECT * FROM shop_categories
WHERE shop_no = 1 AND category_path LIKE '1/%'
ORDER BY category_path ASC;

-- 결과: 1, 1/27, 1/27/105, 1/27/106, 1/28, ...
```

---

## 🧪 사용 예시

### **1. 카테고리 생성 (최상위)**
```bash
POST /api/v1/categories/shops/1
Authorization: Bearer {token}

{
  "category_name": "의류",
  "category_code": "clothing",
  "use_display": true,
  "hash_tags": ["패션", "옷"],
  "meta_keywords": "의류,패션,옷"
}

# Response
{
  "category_no": 1,
  "category_depth": 1,
  "category_path": "1/",
  "full_category_name": "의류"
}
```

### **2. 카테고리 생성 (하위)**
```bash
POST /api/v1/categories/shops/1
{
  "category_name": "하의",
  "parent_category_no": 1,
  "category_code": "bottoms"
}

# Response
{
  "category_no": 27,
  "parent_category_no": 1,
  "category_depth": 2,
  "category_path": "1/27/",
  "full_category_name": "의류 > 하의"
}
```

### **3. Tree 구조 조회**
```bash
GET /api/v1/categories/shops/1/tree?use_display=true

# Response (재귀 구조)
[
  {
    "category_no": 1,
    "category_name": "의류",
    "children": [
      {
        "category_no": 27,
        "category_name": "하의",
        "children": [
          {
            "category_no": 105,
            "category_name": "청바지",
            "children": []
          }
        ]
      }
    ]
  }
]
```

### **4. 특정 깊이 카테고리 조회**
```bash
GET /api/v1/categories/shops/1/depth/2?use_display=true

# 중분류만 조회 (하의, 상의, 아우터 등)
```

### **5. 검색**
```bash
GET /api/v1/categories/shops/1/search?keyword=청바지

# category_name 또는 full_category_name에서 검색
```

### **6. Breadcrumb**
```bash
GET /api/v1/categories/shops/1/105/breadcrumb

# Response (상위 카테고리 역순)
[
  {"category_no": 1, "category_name": "의류"},
  {"category_no": 27, "category_name": "하의"},
  {"category_no": 105, "category_name": "청바지"}
]
```

---

## 🔒 비즈니스 규칙

### **1. 생성 제약**
- 최대 4단계까지만 허용
- 삭제된 카테고리 하위에는 생성 불가
- 카테고리 코드 중복 불가 (같은 shop_no 내)

### **2. 삭제 제약**
- 하위 카테고리가 있으면 삭제 불가
- 상품이 등록되어 있으면 삭제 불가 (product_count > 0)
- 기본: Soft Delete (deleted_at)
- Hard Delete: 관리자 전용

### **3. 자동 계산**
- `display_order`: 같은 레벨의 MAX + 1
- `category_depth`: 부모 depth + 1
- `category_path`: 부모 path + "/" + 자신 ID
- `full_category_name`: 상위 카테고리 연결

---

## 📝 Dependencies 추가

`app/api/dependencies.py`:

```python
from app.services.category_service import CategoryService
from app.repositories.category_repository import CategoryRepository

def get_category_service() -> CategoryService:
    category_repository = CategoryRepository()
    return CategoryService(category_repository)
```

## 🔧 Main에 라우터 등록

`app/main.py`:

```python
from app.api.v1 import categories

app.include_router(
    categories.router,
    prefix="/api/v1",
    tags=["categories"]
)
```

---

## 🎨 프론트엔드 활용 예시

### **1. 카테고리 선택 (Dropdown)**
```javascript
// 대분류 조회
GET /api/v1/categories/shops/1/depth/1

// 선택한 대분류의 중분류 조회
GET /api/v1/categories/shops/1/{category_no}/children
```

### **2. 사이드바 메뉴 (Tree)**
```javascript
// 전체 Tree 조회
GET /api/v1/categories/shops/1/tree?use_display=true

// 재귀 렌더링
function renderTree(categories) {
  return categories.map(cat => (
    <li>
      {cat.category_name}
      {cat.children && <ul>{renderTree(cat.children)}</ul>}
    </li>
  ));
}
```

### **3. Breadcrumb 네비게이션**
```javascript
GET /api/v1/categories/shops/1/{category_no}/breadcrumb

// 홈 > 의류 > 하의 > 청바지
```

---

## 🚀 성능 최적화 포인트

### **1. 인덱스 활용**
```sql
-- idx_category_path: 하위 카테고리 조회 (핵심!)
WHERE shop_no = 1 AND category_path LIKE '1/27/%'

-- idx_parent_depth: 직속 자식 조회
WHERE shop_no = 1 AND parent_category_no = 27

-- idx_display: 노출 카테고리 목록
WHERE shop_no = 1 AND use_display = 'T'
```

### **2. 비정규화 필드**
- `product_count`: 배치 업데이트 (매일 또는 실시간)
- `full_category_name`: 미리 계산하여 저장

---

## 🎉 구현 완료!

계층형 카테고리 시스템이 완성되었습니다!
- Path 기반 계층 구조 ✅
- 멀티샵 지원 ✅
- Tree/Flat 변환 ✅
- Breadcrumb ✅
- 검색 최적화 ✅