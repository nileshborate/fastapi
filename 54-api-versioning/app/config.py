# Settings: when v1 became deprecated, and when it stops working (both can come from env vars)
from datetime import UTC, datetime
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    v1_deprecated_at: datetime = datetime(2026, 11, 1, tzinfo=UTC)
    v1_sunset_at: datetime = datetime(2027, 5, 1, tzinfo=UTC)        # 6 months later
    deprecation_docs: str = "https://coursehub.example/docs/v1-sunset"     # your notice page


@lru_cache
def get_settings() -> Settings:
    return Settings()
