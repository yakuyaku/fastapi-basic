from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Environment
    ENVIRONMENT: str = "development"

    # Database - 기본값 추가
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306  # 기본값 추가!
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "railway"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Development Only
    DEV_ACCESS_TOKEN: Optional[str] = None

    # Logging
    LOG_DIR: str = "/app/logs"
    LOG_LEVEL: str = "INFO"
    LOG_TO_CONSOLE: bool = True
    LOG_MAX_SIZE: int = 52428800
    LOG_BACKUP_COUNT: int = 90

    # File Upload
    UPLOAD_DIR: str = "/app/uploads"
    MAX_IMAGE_SIZE: int = 10485760
    MAX_DOCUMENT_SIZE: int = 52428800

    # CORS
    CORS_ORIGINS: str = '["http://localhost:3000"]'

    # Application
    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_RATE_LIMIT: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = SettingsConfigDict(
        env_file=".env" if os.getenv("RAILWAY_ENVIRONMENT_NAME") is None else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        """데이터베이스 연결 URL"""
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS origins를 리스트로 변환"""
        import json
        return json.loads(self.CORS_ORIGINS)

    @property
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """운영 환경 여부"""
        return self.ENVIRONMENT == "production"

    @property
    def is_railway(self) -> bool:
        """Railway 환경 여부"""
        return os.getenv("RAILWAY_ENVIRONMENT_NAME") is not None


# 전역 설정 인스턴스
settings = Settings()