from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Database
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # Logging
    LOG_DIR: str
    LOG_LEVEL: str
    LOG_TO_CONSOLE: bool
    LOG_MAX_SIZE: int
    LOG_BACKUP_COUNT: int

    # Security (JWT)
    SECRET_KEY: str = "default-secret-key"  # 기본값 설정
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_IMAGE_SIZE: int = 10485760  # 10MB
    MAX_DOCUMENT_SIZE: int = 52428800  # 50MB

    # CORS
    CORS_ORIGINS: str = '["http://localhost:3000"]'

    # Application Settings
    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_RATE_LIMIT: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # 추가 필드 무시
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


# 전역 설정 인스턴스
settings = Settings()