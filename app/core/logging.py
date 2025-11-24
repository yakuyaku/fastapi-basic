"""
일자별 로그 파일 생성
app/core/logging.py
"""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
from app.core.config import settings


def setup_logging():
    """일자별 로깅 설정"""
    logger = logging.getLogger("fastapi_app")
    logger.setLevel(settings.LOG_LEVEL)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 콘솔 핸들러
    if settings.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(settings.LOG_LEVEL)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 일자별 파일 핸들러
    try:
        log_dir = Path(settings.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)

        # 오늘 날짜로 파일명 생성
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = log_dir / f"app_{today}.log"

        file_handler = TimedRotatingFileHandler(
            filename=str(log_file),
            when='midnight',      # 자정에 로테이션
            interval=1,           # 1일마다
            backupCount=30,       # 30일 보관
            encoding='utf-8',
            utc=False
        )

        file_handler.setLevel(settings.LOG_LEVEL)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info(f"✅ 로그 파일: {log_file}")

    except Exception as e:
        logger.warning(f"⚠️ 파일 로깅 실패: {str(e)}")

    return logger


logger = setup_logging()