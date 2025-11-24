from fastapi import FastAPI
from app.api import users
from app.core.config import settings
from app.core.logging import logger
from app.middleware.request_id import RequestIdMiddleware  # 추가
from app.middleware.logging import LoggingMiddleware, DetailedLoggingMiddleware

# FastAPI 앱 생성
app = FastAPI(
    title="사용자 관리 API",
    description="FastAPI 학습용 사용자 관리 시스템",
    version="1.0.0"
)


# 2. LoggingMiddleware 나중에 등록
if settings.ENVIRONMENT == "development":
    app.add_middleware(DetailedLoggingMiddleware)
    logger.info("✅ DetailedLoggingMiddleware 등록 완료")
else:
    app.add_middleware(LoggingMiddleware)
    logger.info("✅ LoggingMiddleware 등록 완료")
# ⭐ 중요: 미들웨어는 역순으로 실행되므로 순서 주의!
# 1. RequestIdMiddleware 먼저 등록 (가장 먼저 실행되어야 함)
app.add_middleware(RequestIdMiddleware)

# 라우터 등록
app.include_router(users.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 이벤트"""
    logger.info("=" * 60)
    logger.info("🚀 FastAPI 애플리케이션 시작")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    logger.info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 이벤트"""
    logger.info("🛑 FastAPI 애플리케이션 종료")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "사용자 관리 API에 오신 것을 환영합니다!",
        "docs": "/docs",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}