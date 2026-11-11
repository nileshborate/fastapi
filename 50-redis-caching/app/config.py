# Settings: from environment variables (or a .env file)
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redis_url: str = "redis://localhost:6379/0"    # docker run -d -p 6379:6379 redis:7-alpine
    course_ttl: int = 60                           # seconds: one course stays cached 1 minute
    stats_ttl: int = 30                            # the expensive stats: 30 seconds
    db_delay: float = 0.3                          # our "slow database query"


@lru_cache
def get_settings() -> Settings:
    return Settings()
