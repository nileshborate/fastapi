# Settings: from environment variables (or a .env file)
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redis_url: str = "redis://localhost:6379/0"    # docker run -d -p 6379:6379 redis:7-alpine
    course_ttl: int = 60                           # seconds - plus up to 10% random jitter
    db_delay: float = 0.3                          # our "slow database query"


@lru_cache
def get_settings() -> Settings:
    return Settings()
