# Settings: read from .env (or real environment variables)
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./school.db"
    db_echo: bool = False
    max_courses_per_teacher: int = 3        # NEW: a business rule, in one place


@lru_cache
def get_settings() -> Settings:
    return Settings()
