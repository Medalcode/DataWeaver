import json

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite:///:memory:"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_PRE_PING: bool = True

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    FILE_EXPIRATION_HOURS: int = 24

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def reject_default_secret(cls, v):
        if v in (
            "",
            "change-this-secret-key-in-production",
            "change-this-to-a-random-secret-key-in-production",
            "your-secret-key-change-in-production",
        ):
            import warnings
            warnings.warn(
                "SECRET_KEY is set to a weak or default value. "
                "Set a strong random secret in production."
            )
        return v or "dev-secret-do-not-use-in-production"


settings = Settings()
