import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from datetime import timedelta
from app.core.security import create_access_token

# 개발 전용 사용자 정보
DEV_USER = {
    "user_id": 48,
    "username": "jsyang",
    "email": "jsyang@google.com"
}

# 매우 긴 만료 시간 설정 (30일)
dev_token = create_access_token(
    data=DEV_USER,
    expires_delta=timedelta(days=30)
)

print("\n" + "="*80)
print("🔑 개발 전용 고정 Access Token")
print("="*80)
print(f"\n사용자: {DEV_USER['username']} ({DEV_USER['email']})")
print(f"만료: 30일 후")
print(f"\nToken:\n{dev_token}")
print("\n" + "="*80)
print("\n💡 .env 파일에 다음 내용 추가:")
print(f"DEV_ACCESS_TOKEN={dev_token}")
print("="*80 + "\n")