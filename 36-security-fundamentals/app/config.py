# Settings: read from .env (or real environment variables)
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str = "change-me-in-production"   # signs the tokens - keep it SECRET
    token_minutes: int = 15                       # a token lives 15 minutes
    session_minutes: int = 30                     # a session cookie lives 30 minutes
    cookie_secure: bool = False                   # True in production (HTTPS only)


@lru_cache
def get_settings() -> Settings:
    return Settings()
