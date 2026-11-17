# Settings: what we depend on, and how long a health check may take
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    version: str = "1.4.0"
    db_path: str = "coursehub.db"
    payments_url: str = "http://127.0.0.1:8057"     # another service we call
    check_timeout: float = 1.0                       # seconds - a health check must be FAST


@lru_cache
def get_settings() -> Settings:
    return Settings()
