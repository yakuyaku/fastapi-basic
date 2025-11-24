# JWT 인증 시스템 구현 정리

## 📋 개요

FastAPI에서 JWT(JSON Web Token) 기반 인증 시스템을 성공적으로 구현했습니다.
사용자 로그인, 토큰 발급, 토큰 검증, 권한 기반 접근 제어가 가능합니다.

---

## 🏗️ 아키텍처

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│  Frontend   │ ───> │   FastAPI    │ ───> │   Database   │
│             │ <─── │  (Backend)   │ <─── │   (MySQL)    │
└─────────────┘      └──────────────┘      └──────────────┘
     │                      │
     │                      │
  JWT Token          Token 검증 &
  저장 및 전송        사용자 인증
```

---

## 📁 프로젝트 구조

```
app/
├── core/
│   ├── config.py           # 환경 설정 (SECRET_KEY, ALGORITHM 등)
│   ├── security.py         # JWT 생성/검증, 비밀번호 해싱
│   └── dependencies.py     # 인증 의존성 (get_current_user 등)
├── api/
│   ├── auth.py            # 인증 API (로그인, /me, 로그아웃)
│   └── users.py           # 사용자 API (보호된 엔드포인트 포함)
├── schemas/
│   └── auth.py            # 인증 관련 스키마
└── main.py                # CORS 설정 포함
```

---

## 🔑 핵심 컴포넌트

### 1. JWT 토큰 생성 (`app/core/security.py`)

```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT Access Token 생성
    - 사용자 정보를 포함한 토큰 생성
    - 만료 시간 설정 (기본: 30분)
    - HS256 알고리즘 사용
    """
```

**포함되는 정보:**
- `user_id`: 사용자 ID
- `username`: 사용자명
- `email`: 이메일
- `exp`: 만료 시간 (expiration)

### 2. JWT 토큰 검증 (`app/core/security.py`)

```python
def decode_access_token(token: str) -> Optional[dict]:
    """
    JWT Access Token 디코딩 및 검증
    - 토큰 유효성 검사
    - 만료 시간 확인
    - 서명 검증
    """
```

### 3. 인증 의존성 (`app/core/dependencies.py`)

```python
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    현재 인증된 사용자 가져오기
    1. Authorization 헤더에서 토큰 추출
    2. 토큰 검증
    3. 사용자 정보 조회
    4. 활성 상태 확인
    """
```

```python
async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    """
    관리자 권한 확인
    - 인증된 사용자 중 관리자만 통과
    """
```

---

## 🔐 인증 흐름

### 로그인 프로세스

```
1. 사용자가 email + password 전송
   ↓
2. 서버에서 사용자 조회 (DB)
   ↓
3. 비밀번호 검증 (bcrypt)
   ↓
4. JWT 토큰 생성
   ↓
5. 토큰 + 사용자 정보 응답
   ↓
6. 클라이언트에서 토큰 저장 (localStorage)
```

### 인증이 필요한 API 호출

```
1. 클라이언트가 Authorization 헤더에 토큰 포함
   Authorization: Bearer <token>
   ↓
2. 미들웨어/의존성에서 토큰 검증
   ↓
3. 토큰 유효 → 사용자 정보 조회
   ↓
4. 활성 사용자 확인
   ↓
5. API 처리 및 응답
```

---

## 🛣️ API 엔드포인트

### 인증 API (`/api/auth`)

| 메서드 | 경로 | 설명 | 인증 필요 |
|--------|------|------|-----------|
| POST | `/api/auth/login` | 로그인 (토큰 발급) | ❌ |
| GET | `/api/auth/me` | 현재 사용자 정보 조회 | ✅ |
| POST | `/api/auth/logout` | 로그아웃 | ✅ |

### 보호된 사용자 API 예제

| 메서드 | 경로 | 설명 | 권한 |
|--------|------|------|------|
| GET | `/api/users/me/profile` | 내 프로필 조회 | 인증 필요 |
| GET | `/api/users/admin/all` | 모든 사용자 조회 | 관리자 전용 |

---

## 💻 사용 예제

### 1. 로그인 (토큰 발급)

**요청:**
```bash
curl -X POST "http://127.0.0.1:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**응답:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6InRlc3R1c2VyIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzAwMDAwMDAwfQ.abc123...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "testuser",
    "is_admin": false
  }
}
```

### 2. 인증이 필요한 API 호출

**요청:**
```bash
curl -X GET "http://127.0.0.1:8000/api/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**응답:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "testuser",
  "is_active": true,
  "is_admin": false,
  "created_at": "2025-11-24T10:00:00"
}
```

### 3. 토큰 없이 호출 (실패)

**요청:**
```bash
curl -X GET "http://127.0.0.1:8000/api/auth/me"
```

**응답:**
```json
{
  "detail": "Not authenticated"
}
```

### 4. 관리자 전용 API (권한 부족 시)

**요청:**
```bash
curl -X GET "http://127.0.0.1:8000/api/users/admin/all" \
  -H "Authorization: Bearer <일반_사용자_토큰>"
```

**응답:**
```json
{
  "detail": "관리자 권한이 필요합니다"
}
```

---

## 🌐 Frontend 연동

### JavaScript/React 예제

#### 1. 로그인 함수

```javascript
async function login(email, password) {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });
    
    const data = await response.json();
    
    if (response.ok) {
      // 토큰 저장
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      console.log('로그인 성공:', data.user);
      return data;
    } else {
      console.error('로그인 실패:', data.detail);
      throw new Error(data.detail);
    }
  } catch (error) {
    console.error('로그인 오류:', error);
    throw error;
  }
}
```

#### 2. 인증 API 호출 함수

```javascript
async function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem('access_token');
  
  if (!token) {
    throw new Error('로그인이 필요합니다');
  }
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  
  if (response.status === 401) {
    // 토큰 만료 또는 유효하지 않음
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
    throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
  }
  
  return response;
}
```

#### 3. 현재 사용자 정보 조회

```javascript
async function getCurrentUser() {
  try {
    const response = await fetchWithAuth('http://127.0.0.1:8000/api/auth/me');
    
    if (response.ok) {
      const user = await response.json();
      console.log('현재 사용자:', user);
      return user;
    }
  } catch (error) {
    console.error('사용자 정보 조회 실패:', error);
  }
}
```

#### 4. 로그아웃

```javascript
function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  window.location.href = '/login';
}
```

#### 5. React Hook 예제

```javascript
import { useState, useEffect } from 'react';

function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
    
    setLoading(false);
  }, []);
  
  const login = async (email, password) => {
    const response = await fetch('http://127.0.0.1:8000/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    
    const data = await response.json();
    
    if (response.ok) {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      setUser(data.user);
    } else {
      throw new Error(data.detail);
    }
  };
  
  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
  };
  
  return { user, loading, login, logout };
}

// 사용 예제
function App() {
  const { user, loading, login, logout } = useAuth();
  
  if (loading) return <div>로딩 중...</div>;
  
  if (!user) {
    return <LoginForm onLogin={login} />;
  }
  
  return (
    <div>
      <h1>환영합니다, {user.username}님!</h1>
      <button onClick={logout}>로그아웃</button>
    </div>
  );
}
```

---

## 🔒 보안 설정

### 환경 변수 (`.env`)

```env
# JWT 설정
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 설정
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

### SECRET_KEY 생성 방법

```python
# Python에서 안전한 SECRET_KEY 생성
import secrets
print(secrets.token_urlsafe(32))
# 출력: 'dQw4w9WgXcQ_fNXz7yU-jK8vL9mN0oP1qR2sT3uV4wX'
```

### CORS 설정

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 토큰 구조

### JWT 토큰 예제

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6InRlc3R1c2VyIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzAwMDAwMDAwfQ.abc123def456...
```

### 디코딩된 페이로드

```json
{
  "user_id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "exp": 1700000000
}
```

**구성 요소:**
1. **Header**: 알고리즘 정보 (HS256)
2. **Payload**: 사용자 정보 + 만료 시간
3. **Signature**: SECRET_KEY로 서명

---

## 🛡️ 보안 기능

### 1. 비밀번호 보안
- ✅ **bcrypt 해싱** - 단방향 암호화 (rounds=12)
- ✅ **Salt 자동 생성** - 각 비밀번호마다 고유한 salt

### 2. 토큰 보안
- ✅ **만료 시간 설정** - 기본 30분
- ✅ **서명 검증** - SECRET_KEY로 위변조 방지
- ✅ **HTTPS 권장** - 운영 환경에서 필수

### 3. 접근 제어
- ✅ **인증 확인** - 토큰 유효성 검사
- ✅ **활성 사용자 체크** - 비활성화된 계정 차단
- ✅ **권한 기반 접근** - 관리자 전용 API 분리

### 4. CORS 보안
- ✅ **허용된 Origin만 접근** - 설정된 Frontend URL만 허용
- ✅ **Credentials 지원** - 쿠키/인증 헤더 전송 가능

---

## 🔍 인증 흐름 상세

### 로그인 시퀀스 다이어그램

```
Client                  API Server              Database
  |                         |                       |
  |--1. POST /auth/login--->|                       |
  |   {email, password}     |                       |
  |                         |--2. SELECT user------>|
  |                         |<--3. user data--------|
  |                         |                       |
  |                         |--4. verify password   |
  |                         |   (bcrypt)            |
  |                         |                       |
  |                         |--5. create JWT token  |
  |                         |                       |
  |                         |--6. UPDATE last_login->|
  |<--7. {token, user}------|                       |
  |                         |                       |
```

### 인증 API 호출 시퀀스

```
Client                  API Server              Database
  |                         |                       |
  |--1. GET /auth/me------->|                       |
  |   Authorization: Bearer |                       |
  |                         |                       |
  |                         |--2. decode token      |
  |                         |   (verify signature)  |
  |                         |                       |
  |                         |--3. SELECT user------>|
  |                         |<--4. user data--------|
  |                         |                       |
  |                         |--5. check is_active   |
  |                         |                       |
  |<--6. user info----------|                       |
  |                         |                       |
```

---

## ⚠️ 에러 처리

### 인증 관련 에러 코드

| 상태 코드 | 에러 | 설명 |
|----------|------|------|
| 401 | Unauthorized | 토큰 없음/유효하지 않음/만료됨 |
| 403 | Forbidden | 권한 부족 (비활성 계정, 관리자 아님) |
| 404 | Not Found | 사용자를 찾을 수 없음 |
| 500 | Internal Server Error | 서버 내부 오류 |

### 에러 응답 예제

```json
{
  "detail": "유효하지 않은 인증 정보입니다"
}
```

---

## 📝 로그 예제

### 성공적인 로그인

```
2025-11-24 11:00:00 - fastapi_app - INFO - [abc-123] → POST http://127.0.0.1:8000/api/auth/login
2025-11-24 11:00:00 - fastapi_app - INFO - [abc-123] 로그인 요청 - email: test@example.com
2025-11-24 11:00:00 - fastapi_app - INFO - [abc-123] 로그인 성공 - ID: 1, username: testuser
2025-11-24 11:00:00 - fastapi_app - INFO - [abc-123] ← POST http://127.0.0.1:8000/api/auth/login - Status: 200 - Duration: 0.125s
```

### 실패한 로그인

```
2025-11-24 11:00:05 - fastapi_app - INFO - [def-456] → POST http://127.0.0.1:8000/api/auth/login
2025-11-24 11:00:05 - fastapi_app - INFO - [def-456] 로그인 요청 - email: wrong@example.com
2025-11-24 11:00:05 - fastapi_app - WARNING - [def-456] 로그인 실패 - email: wrong@example.com
2025-11-24 11:00:05 - fastapi_app - INFO - [def-456] ← POST http://127.0.0.1:8000/api/auth/login - Status: 401 - Duration: 0.089s
```

### 인증 API 호출

```
2025-11-24 11:01:00 - fastapi_app - INFO - [ghi-789] → GET http://127.0.0.1:8000/api/auth/me
2025-11-24 11:01:00 - fastapi_app - INFO - [ghi-789] 현재 사용자 조회 - ID: 1
2025-11-24 11:01:00 - fastapi_app - INFO - [ghi-789] ← GET http://127.0.0.1:8000/api/auth/me - Status: 200 - Duration: 0.015s
```

---

## 🧪 테스트 시나리오

### 1. 정상 로그인 → API 호출

```bash
# 1. 로그인
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' \
  | jq -r '.access_token')

# 2. 토큰 확인
echo $TOKEN

# 3. 인증 API 호출
curl -X GET "http://127.0.0.1:8000/api/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

### 2. 잘못된 비밀번호

```bash
curl -X POST "http://127.0.0.1:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"wrongpassword"}'

# 예상 응답: 401 Unauthorized
```

### 3. 토큰 없이 보호된 API 호출

```bash
curl -X GET "http://127.0.0.1:8000/api/auth/me"

# 예상 응답: 401 Not authenticated
```

### 4. 일반 사용자가 관리자 API 호출

```bash
# 일반 사용자 토큰으로
curl -X GET "http://127.0.0.1:8000/api/users/admin/all" \
  -H "Authorization: Bearer $TOKEN"

# 예상 응답: 403 Forbidden
```

---

## 🎯 Best Practices

### 1. 토큰 저장
- ✅ **localStorage** - SPA에서 간단하게 사용
- ✅ **sessionStorage** - 탭 닫으면 자동 삭제
- ⚠️ **쿠키** - HttpOnly 플래그 필수 (XSS 방지)

### 2. 토큰 만료 처리
- 401 응답 받으면 자동 로그아웃
- 리프레시 토큰 도입 고려 (추후 개선)

### 3. HTTPS 사용
- 운영 환경에서는 HTTPS 필수
- 토큰이 평문으로 전송되므로

### 4. 비밀번호 정책
- 최소 8자 이상
- 영문 + 숫자 조합
- 특수문자 포함 권장

### 5. SECRET_KEY 관리
- 절대 코드에 하드코딩 금지
- 환경 변수로 관리
- 주기적으로 변경

---

## 🚀 향후 개선 사항

### 1. Refresh Token 구현
```python
# 장기 토큰 (7일)
refresh_token = create_refresh_token(user_id)

# Access Token 갱신
new_access_token = refresh_access_token(refresh_token)
```

### 2. 토큰 블랙리스트
```python
# 로그아웃 시 토큰 무효화
blacklist.add(token)

# 토큰 검증 시 블랙리스트 확인
if token in blacklist:
    raise UnauthorizedException()
```

### 3. 다중 기기 로그인 관리
```python
# 사용자별 활성 세션 추적
sessions = get_user_sessions(user_id)

# 특정 세션 종료
invalidate_session(session_id)
```

### 4. OAuth 2.0 소셜 로그인
- Google 로그인
- GitHub 로그인
- 카카오 로그인

### 5. 2FA (Two-Factor Authentication)
- TOTP (Time-based OTP)
- SMS 인증
- 이메일 인증

---

## 📚 참고 자료

- [JWT 공식 사이트](https://jwt.io/)
- [FastAPI 보안 문서](https://fastapi.tiangolo.com/tutorial/security/)
- [OAuth 2.0 RFC](https://datatracker.ietf.org/doc/html/rfc6749)
- [bcrypt 문서](https://github.com/pyca/bcrypt/)

---

## ✅ 구현 완료 체크리스트

- [x] JWT 토큰 생성 기능
- [x] JWT 토큰 검증 기능
- [x] 로그인 API
- [x] 현재 사용자 조회 API
- [x] 로그아웃 API
- [x] 인증 의존성 (get_current_user)
- [x] 관리자 권한 의존성 (get_current_admin_user)
- [x] CORS 설정
- [x] 비밀번호 해싱 (bcrypt)
- [x] 마지막 로그인 시간 기록
- [x] 활성 사용자 체크
- [x] 에러 처리
- [x] 로깅

---

**마지막 업데이트:** 2025-11-24  
**작성자:** jsyang  
**버전:** 1.0.0