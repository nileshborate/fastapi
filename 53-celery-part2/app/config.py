# Settings: from environment variables (or a .env file)
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"
    redis_url: str = "redis://localhost:6379/0"      # homework 53: our own small notes
    email_seconds: float = 0.2                     # one email
    email_fail_times: int = 2                      # the email server fails 2 times, then works
    step_seconds: float = 0.5                      # one step of a report


@lru_cache
def get_settings() -> Settings:
    return Settings()
