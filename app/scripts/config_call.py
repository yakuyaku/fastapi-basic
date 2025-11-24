import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings

# 데이터베이스 URL 가져오기
db_url = settings.database_url

# 로그 레벨 가져오기
log_level = settings.LOG_LEVEL

print(f"DB: {settings.DB_HOST}")
print(f"LOG: {settings.LOG_LEVEL}")
print(f"db_url: {db_url}")