# Settings from the environment - the SAME DATABASE_URL for the api and for Alembic
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    version: str = "1.11.0"
    database_url: str                # postgresql://user:password@host:5432/database
    db_wait_s: float = 10            # how long the app waits for PostgreSQL at startup
    migration_lock_timeout: str = "5s"   # a migration waits at most this long for a table lock


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]   # the value comes from the environment
