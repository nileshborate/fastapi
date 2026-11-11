# Settings: read from .env (or real environment variables)
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./school.db"
    db_echo: bool = False
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    environment: Literal["development", "production"] = "development"
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]   # Host header
    cors_origins: list[str] = ["http://localhost:3000"]                   # browsers only
    max_body_bytes: int = 16 * 1024            # 16 KB - more than any of our JSON bodies
    login_limit: int = 5                       # 5 login tries ...
    login_window_seconds: int = 60             # ... per minute, per IP and email
    domain_limit: int = 3                      # homework 45: 3 new accounts ...
    domain_window_seconds: int = 3600          # ... per hour, per email domain

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
