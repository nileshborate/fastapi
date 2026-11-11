# Settings: read from .env (or real environment variables)
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./school.db"
    db_echo: bool = False
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    frontend_url: str = "http://localhost:3000"     # the links in the emails go here
    verify_link_hours: int = 24                     # "verify your email" - a whole day
    reset_link_minutes: int = 30                    # "reset your password" - short!


@lru_cache
def get_settings() -> Settings:
    return Settings()
