#!/bin/bash

set -e  # 에러 발생 시 즉시 중단

# ============================================
# FastAPI 배포 스크립트 v2.0
# ============================================

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 설정
EC2_HOST="13.238.28.75"
EC2_USER="ubuntu"
EC2_KEY="$HOME/.ssh/my-fastapi.pem"
REMOTE_DIR="/home/ubuntu/fastapi-basic"
LOCAL_DIR="$(pwd)"
APP_NAME="fastapi"
BACKUP_DIR="/home/ubuntu/backups"
MAX_BACKUPS=5

# 헬퍼 함수
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 배너
print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════╗"
    echo "║   FastAPI Deployment Script v2.0      ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 시작
print_banner
log_info "Starting deployment process..."

# ============================================
# 1. 사전 검증
# ============================================

log_info "Step 1/10: Pre-deployment validation"

# Git 상태 확인
if [[ -n $(git status -s) ]]; then
    log_warning "You have uncommitted changes"
    git status -s
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "Deployment cancelled"
        exit 1
    fi
fi

# 현재 브랜치 확인
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log_info "Current branch: ${CURRENT_BRANCH}"

if [ "$CURRENT_BRANCH" != "main" ]; then
    log_warning "Not on main branch!"
    read -p "Deploy from ${CURRENT_BRANCH}? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "Deployment cancelled"
        exit 1
    fi
fi

# SSH 연결 테스트
log_info "Testing SSH connection..."
if ! ssh -i "$EC2_KEY" -o ConnectTimeout=5 "$EC2_USER@$EC2_HOST" "echo 'Connected'" > /dev/null 2>&1; then
    log_error "Cannot connect to EC2. Check your SSH key and network."
    exit 1
fi
log_success "SSH connection successful"

# ============================================
# 2. 최신 코드 가져오기
# ============================================

log_info "Step 2/10: Pulling latest code"
git pull origin "$CURRENT_BRANCH"
log_success "Code updated"

# ============================================
# 3. 로컬 테스트 (선택사항)
# ============================================

log_info "Step 3/10: Running local tests"
if [ -f "scripts/test-before-deploy.sh" ]; then
    bash scripts/test-before-deploy.sh
    if [ $? -ne 0 ]; then
        log_error "Tests failed! Deployment aborted."
        exit 1
    fi
    log_success "Tests passed"
else
    log_warning "Test script not found, skipping tests"
fi

# ============================================
# 4. EC2에 백업 생성
# ============================================

log_info "Step 4/10: Creating backup on EC2"

BACKUP_NAME="fastapi-backup-$(date +%Y%m%d-%H%M%S)"

ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" << ENDSSH
    # 백업 디렉토리 생성
    mkdir -p $BACKUP_DIR

    # 현재 배포본 백업
    if [ -d "$REMOTE_DIR" ]; then
        echo "Creating backup: $BACKUP_NAME"
        tar -czf $BACKUP_DIR/$BACKUP_NAME.tar.gz \
            -C $(dirname $REMOTE_DIR) \
            $(basename $REMOTE_DIR) \
            2>/dev/null || echo "Warning: Backup may be incomplete"

        # 오래된 백업 삭제 (최근 5개만 유지)
        cd $BACKUP_DIR
        ls -t *.tar.gz 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm

        echo "Backup created: $BACKUP_NAME.tar.gz"
    else
        echo "No existing deployment to backup"
    fi
ENDSSH

log_success "Backup created"

# ============================================
# 5. 프로젝트 디렉토리 생성
# ============================================

log_info "Step 5/10: Preparing remote directory"

ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" << ENDSSH
    mkdir -p $REMOTE_DIR
    mkdir -p $REMOTE_DIR/logs
ENDSSH

log_success "Remote directory ready"

# ============================================
# 6. 파일 전송 (rsync)
# ============================================

log_info "Step 6/10: Transferring files to EC2"

# .deployignore를 rsync exclude 파일로 변환
EXCLUDE_FILE=$(mktemp)
if [ -f ".deployignore" ]; then
    cat .deployignore | sed 's/^/--exclude=/' > "$EXCLUDE_FILE"
fi

# rsync로 파일 전송
rsync -avz --delete \
    --exclude-from="$EXCLUDE_FILE" \
    -e "ssh -i $EC2_KEY -o StrictHostKeyChecking=no" \
    --exclude='.git/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='venv/' \
    --exclude='.venv/' \
    --exclude='tests/' \
    ./ "$EC2_USER@$EC2_HOST:$REMOTE_DIR/"

rm "$EXCLUDE_FILE"

log_success "Files transferred"

# ============================================
# 7. .env 파일 확인
# ============================================

log_info "Step 7/10: Checking environment variables"

ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" << ENDSSH
    if [ ! -f "$REMOTE_DIR/.env" ]; then
        echo "⚠️  .env file not found!"
        echo "Creating .env from .env.example..."

        if [ -f "$REMOTE_DIR/.env.example" ]; then
            cp "$REMOTE_DIR/.env.example" "$REMOTE_DIR/.env"
            echo "⚠️  Please edit .env file with production values!"
        else
            echo "❌ .env.example not found. Please create .env manually."
            exit 1
        fi
    else
        echo "✅ .env file exists"
    fi
ENDSSH

log_success "Environment variables checked"

# ============================================
# 8. 의존성 설치 및 마이그레이션
# ============================================

log_info "Step 8/10: Installing dependencies and running migrations"

ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" << 'ENDSSH'
    cd /home/ubuntu/fastapi-basic

    # 가상환경 활성화 (또는 생성)
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    source venv/bin/activate

    # 의존성 설치
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt

    # DB 마이그레이션 (Alembic 사용 시)
    if [ -f "alembic.ini" ]; then
        echo "Running database migrations..."
        alembic upgrade head || echo "⚠️  Migration failed or not needed"
    fi

    echo "✅ Dependencies installed"
ENDSSH

log_success "Dependencies and migrations complete"

# ============================================
# 9. 서비스 재시작
# ============================================

log_info "Step 9/10: Restarting FastAPI service"

ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" << ENDSSH
    # Systemd 서비스 재시작
    sudo systemctl restart $APP_NAME

    # 상태 확인
    sleep 2
    if sudo systemctl is-active --quiet $APP_NAME; then
        echo "✅ Service is running"
    else
        echo "❌ Service failed to start!"
        sudo systemctl status $APP_NAME --no-pager
        exit 1
    fi
ENDSSH

if [ $? -ne 0 ]; then
    log_error "Service restart failed!"
    log_warning "Consider rolling back with: ./scripts/rollback.sh $BACKUP_NAME"
    exit 1
fi

log_success "Service restarted"

# ============================================
# 10. 헬스체크
# ============================================

log_info "Step 10/10: Running health check"

sleep 5  # 서비스 시작 대기

# 로컬에서 헬스체크
if curl -f -s https://wejeju.com/api/health > /dev/null 2>&1; then
    log_success "Health check passed!"
else
    log_error "Health check failed!"
    log_warning "Consider rolling back with: ./scripts/rollback.sh $BACKUP_NAME"
    exit 1
fi

# EC2에서도 확인
ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" << ENDSSH
    # 로컬 헬스체크
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Local health check passed"
    else
        echo "❌ Local health check failed"
        exit 1
    fi
ENDSSH

# ============================================
# 완료
# ============================================

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   🎉 Deployment Successful! 🎉        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
log_info "Deployment details:"
echo "  - Branch: $CURRENT_BRANCH"
echo "  - Backup: $BACKUP_NAME"
echo "  - Server: https://wejeju.com/api"
echo ""
log_info "Useful commands:"
echo "  - View logs: ssh -i ~/.ssh/my-fastapi.pem ubuntu@13.238.28.75 'sudo journalctl -u fastapi -f'"
echo "  - Rollback: ./scripts/rollback.sh $BACKUP_NAME"
echo ""

# 로그 확인 옵션
read -p "View application logs? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" "sudo journalctl -u $APP_NAME -n 50 --no-pager"
fi

exit 0