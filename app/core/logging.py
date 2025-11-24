import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.core.config import settings
import functools
import time
from typing import Callable


def setup_logging():
    """로깅 설정"""

    # 로그 디렉토리 생성
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(exist_ok=True)

    # 로거 생성
    logger = logging.getLogger("fastapi_app")
    logger.setLevel(settings.LOG_LEVEL)

    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()

    # 포맷 설정
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 파일 핸들러 (Rotating)
    file_handler = RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=settings.LOG_MAX_SIZE,  # 10MB
        backupCount=settings.LOG_BACKUP_COUNT,  # 30개 백업
        encoding='utf-8'
    )
    file_handler.setLevel(settings.LOG_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 콘솔 핸들러
    if settings.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(settings.LOG_LEVEL)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def log_execution_time(func: Callable):
    """함수 실행 시간 측정 데코레이터"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            logger.info(
                f"[EXECUTION] {func.__name__} - "
                f"Duration: {execution_time:.4f}s"
            )

            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"[EXECUTION ERROR] {func.__name__} - "
                f"Error: {str(e)} - "
                f"Duration: {execution_time:.4f}s"
            )
            raise

    return wrapper

# 전역 로거
logger = setup_logging()