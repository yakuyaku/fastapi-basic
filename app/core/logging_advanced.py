"""
고급 로깅 설정 - 크기 + 시간 기반 로테이션 조합
app/core/logging_advanced.py
"""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from pathlib import Path
from datetime import datetime
from app.core.config import settings


class DailyRotatingFileHandler(TimedRotatingFileHandler):
    """
    커스텀 일자별 로테이션 핸들러
    - 매일 자정에 새 파일 생성
    - 파일명: app_2025-11-24.log
    """

    def __init__(self, log_dir, **kwargs):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 오늘 날짜로 로그 파일 생성
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.log_dir / f"app_{today}.log"

        super().__init__(
            filename=str(log_file),
            when='midnight',
            interval=1,
            backupCount=kwargs.get('backupCount', 30),
            encoding='utf-8',
            utc=False
        )

    def doRollover(self):
        """로테이션 시 새 파일명 생성"""
        super().doRollover()

        # 새로운 날짜로 파일명 변경
        today = datetime.now().strftime('%Y-%m-%d')
        new_log_file = self.log_dir / f"app_{today}.log"
        self.baseFilename = str(new_log_file)


def setup_logging():
    """
    개선된 로깅 설정

    로그 파일 구조:
    logs/
    ├── app_2025-11-24.log  (오늘)
    ├── app_2025-11-23.log  (어제)
    ├── app_2025-11-22.log
    └── ...

    특징:
    - 매일 자정에 새 파일 자동 생성
    - 30일 이상 된 로그 자동 삭제
    - 각 로그 파일 최대 50MB (크기 제한)
    - 콘솔 + 파일 동시 출력
    """
    # 로거 생성
    logger = logging.getLogger("fastapi_app")
    logger.setLevel(settings.LOG_LEVEL)

    # 기존 핸들러 제거
    if logger.hasHandlers():
        logger.handlers.clear()

    # 포맷터 생성
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. 콘솔 핸들러
    if settings.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(settings.LOG_LEVEL)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 2. 일자별 파일 핸들러
    try:
        log_dir = Path(settings.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)

        # 오늘 날짜로 로그 파일명 생성
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = log_dir / f"app_{today}.log"

        # TimedRotatingFileHandler 사용
        file_handler = TimedRotatingFileHandler(
            filename=str(log_file),
            when='midnight',           # 자정에 로테이션
            interval=1,                # 1일마다
            backupCount=30,            # 30일치 보관
            encoding='utf-8',
            utc=False
        )

        # 로테이션된 파일명 형식 설정
        # app.log -> app.log.2025-11-24
        file_handler.suffix = "_%Y-%m-%d"

        file_handler.setLevel(settings.LOG_LEVEL)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info(f"✅ 로그 파일 생성: {log_file}")
        logger.info(f"📁 로그 보관 기간: {30}일")

    except Exception as e:
        logger.warning(f"⚠️ 파일 로깅 설정 실패: {str(e)}")

    return logger


def setup_logging_with_size_limit():
    """
    크기 제한 + 일자별 로테이션 조합

    특징:
    - 매일 자정에 새 파일 생성
    - 각 파일이 50MB 초과 시 추가 로테이션
    - 최대 5개의 백업 파일 (per day)
    """
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

    try:
        log_dir = Path(settings.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)

        # 오늘 날짜로 로그 파일 생성
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = log_dir / f"app_{today}.log"

        # 크기 기반 로테이션 (50MB)
        # app_2025-11-24.log, app_2025-11-24.log.1, app_2025-11-24.log.2, ...
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=5,               # 5개 백업
            encoding='utf-8'
        )

        file_handler.setLevel(settings.LOG_LEVEL)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    except Exception as e:
        logger.warning(f"파일 로깅 설정 실패: {str(e)}")

    return logger


# 전역 로거 인스턴스
logger = setup_logging()