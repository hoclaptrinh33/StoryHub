from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
    )

    app_name: str = Field(default="StoryHub Backend", validation_alias="STORYHUB_APP_NAME")
    app_version: str = Field(default="0.1.0", validation_alias="STORYHUB_APP_VERSION")
    environment: str = Field(default="development", validation_alias="STORYHUB_ENVIRONMENT")
    log_level: str = Field(default="INFO", validation_alias="STORYHUB_LOG_LEVEL")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./storyhub.db",
        validation_alias="STORYHUB_DATABASE_URL",
    )
    cors_allow_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="STORYHUB_CORS_ALLOW_ORIGINS",
    )

    reservation_timeout_minutes: int = Field(
        default=30,
        ge=1,
        le=240,
        validation_alias="STORYHUB_RESERVATION_TIMEOUT_MINUTES",
    )
    scanner_buffer_timeout_ms: int = Field(
        default=50,
        ge=20,
        le=200,
        validation_alias="STORYHUB_SCANNER_BUFFER_TIMEOUT_MS",
    )
    item_lock_timeout_ms: int = Field(
        default=2000,
        ge=100,
        le=10000,
        validation_alias="STORYHUB_ITEM_LOCK_TIMEOUT_MS",
    )
    idempotency_window_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        validation_alias="STORYHUB_IDEMPOTENCY_WINDOW_HOURS",
    )
    overdue_fee_per_day: float = Field(
        default=5000,
        ge=0,
        le=100000,
        validation_alias="STORYHUB_OVERDUE_FEE_PER_DAY",
    )
    damage_fee_minor_percent: float = Field(
        default=20,
        ge=0,
        le=100,
        validation_alias="STORYHUB_DAMAGE_FEE_MINOR_PERCENT",
    )
    damage_fee_major_percent: float = Field(
        default=50,
        ge=0,
        le=100,
        validation_alias="STORYHUB_DAMAGE_FEE_MAJOR_PERCENT",
    )

    @property
    def cors_allow_origins(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_allow_origins_raw.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
