from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import users, auth, posts, files  # Clean Architecture v1 라우터
from app.core.config import settings
from app.core.logging import logger
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.logging import LoggingMiddleware, DetailedLoggingMiddleware

app = FastAPI(
    title="사용자 관리 API",
    description="FastAPI 사용자, 게시글, 파일, 코멘트 Backend 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 미들웨어
if settings.ENVIRONMENT == "development":
    app.add_middleware(DetailedLoggingMiddleware)
    logger.info("✅ DetailedLoggingMiddleware 등록 완료")
else:
    app.add_middleware(LoggingMiddleware)
    logger.info("✅ LoggingMiddleware 등록 완료")

# Request ID 미들웨어
app.add_middleware(RequestIdMiddleware)
logger.info("✅ RequestIdMiddleware 등록 완료")

# 라우터 등록
app.include_router(auth.router, prefix="/api")  # 인증 라우터 추가
app.include_router(users.router, prefix="/api")
app.include_router(
    posts.router,
    prefix="/api/v1",
    tags=["posts"]
)

app.include_router(
    files.router,
    prefix="/api/v1",
    tags=["files"]
)

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
        "message": "FASTTAPI에 오신 것을 환영합니다!",
        "docs": "/docs",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}

@app.get("/dev-info")
async def dev_info():
    """개발 환경 정보 (개발 환경에서만)"""
    if not settings.is_development:
        raise HTTPException(status_code=403, detail="개발 환경에서만 사용 가능")

    token_info = None
    if settings.DEV_ACCESS_TOKEN:
        from app.core.security import decode_access_token
        payload = decode_access_token(settings.DEV_ACCESS_TOKEN)
        if payload:
            from datetime import datetime
            exp_timestamp = payload.get('exp')
            exp_date = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None
            token_info = {
                "user_id": payload.get('user_id'),
                "username": payload.get('username'),
                "email": payload.get('email'),
                "expires_at": exp_date.isoformat() if exp_date else None
            }

    return {
        "environment": settings.ENVIRONMENT,
        "dev_token_configured": settings.DEV_ACCESS_TOKEN is not None,
        "dev_token_info": token_info
    }