# Settings - DATABASE_URL has NO default: without it, the app refuses to start
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    version: str = "1.7.0"
    database_url: str                # postgresql://user:password@host:5432/database
    db_wait_s: float = 10            # how long the app waits for PostgreSQL at startup


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]   # the value comes from the environment
