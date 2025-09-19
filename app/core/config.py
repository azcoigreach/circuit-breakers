from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application configuration."""

    env: Literal["dev", "test", "prod"] = Field("dev", alias="APP_ENV")
    debug: bool = Field(False, alias="APP_DEBUG")
    database_url: str = Field(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/circuit_breakers",
        alias="DATABASE_URL",
    )
    test_database_url: str = Field(
        "sqlite+aiosqlite:///:memory:", alias="TEST_DATABASE_URL"
    )
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    tick_interval_seconds: float = Field(1.0, alias="TICK_INTERVAL_SECONDS")
    ruleset: str = Field("season1_dark_grid", alias="RULESET")
    request_log_sample_rate: float = Field(1.0, alias="REQUEST_LOG_SAMPLE_RATE")
    dev_mode: bool = Field(True, alias="DEV_MODE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
