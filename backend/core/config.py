from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/core/config.py -> project root is two levels up
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Evidentra Platform"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    log_level: str = "INFO"
    seed_on_startup: bool = Field(default=True, validation_alias="SEED_ON_STARTUP")

    seed_admin_username: str | None = Field(default=None, validation_alias="SEED_ADMIN_USERNAME")
    seed_admin_email: str | None = Field(default=None, validation_alias="SEED_ADMIN_EMAIL")
    seed_admin_password: str | None = Field(default=None, validation_alias="SEED_ADMIN_PASSWORD")

    seed_investigator_username: str | None = Field(
        default=None,
        validation_alias="SEED_INVESTIGATOR_USERNAME",
    )
    seed_investigator_email: str | None = Field(
        default=None,
        validation_alias="SEED_INVESTIGATOR_EMAIL",
    )
    seed_investigator_password: str | None = Field(
        default=None,
        validation_alias="SEED_INVESTIGATOR_PASSWORD",
    )

    database_url: str = Field(
        default="sqlite:///./evidentra.db",
        validation_alias="DATABASE_URL",
    )

    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    jwt_secret_key: str = Field(
        default="change-me-in-development-only",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        validation_alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS",
    )

    allowed_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        validation_alias="ALLOWED_ORIGINS",
    )

    storage_path: str = Field(default="./data/uploads", validation_alias="STORAGE_PATH")
    max_upload_size_mb: int = Field(default=100, validation_alias="MAX_UPLOAD_SIZE_MB")
    adb_path: str = Field(default="adb", validation_alias="ADB_PATH")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_adb_path() -> str:
    return get_settings().adb_path


def get_project_root() -> Path:
    return PROJECT_ROOT
