#!/bin/bash

set -e

# EC2에서 실행하는 배포 스크립트

echo "🚀 FastAPI Deployment on EC2"

REMOTE_DIR="/home/ubuntu/fastapi-basic"
BRANCH="${1:-main}"

cd "$REMOTE_DIR"

# Git 업데이트
echo "📦 Pulling latest code from $BRANCH..."
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

# 가상환경 활성화
source venv/bin/activate

# 의존성 업데이트
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# DB 마이그레이션
if [ -f "alembic.ini" ]; then
    echo "🗄️  Running migrations..."
    alembic upgrade head
fi

# 서비스 재시작
echo "🔄 Restarting service..."
sudo systemctl restart fastapi

# 상태 확인
sleep 2
sudo systemctl status fastapi --no-pager

echo "✅ Deployment complete!"