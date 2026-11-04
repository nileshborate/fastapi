# Settings: read from .env (or real environment variables)
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./school.db"
    db_echo: bool = False
    # NEW: the connection pool
    pool_size: int = 5          # connections kept open
    max_overflow: int = 10      # extra connections in a rush (closed again later)
    pool_timeout: float = 30    # seconds to wait for a free connection - then an error


@lru_cache
def get_settings() -> Settings:
    return Settings()
