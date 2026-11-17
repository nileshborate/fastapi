# Settings: from environment variables (or a .env file)
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    broker_url: str = "redis://localhost:6379/0"       # the QUEUE: where tasks wait
    result_backend: str = "redis://localhost:6379/1"   # where results and states are kept
    email_seconds: float = 2.0                         # our "slow" email server
    report_step_seconds: float = 0.5                   # a report has 5 steps


@lru_cache
def get_settings() -> Settings:
    return Settings()
