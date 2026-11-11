# Settings: read from .env (or real environment variables)
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15


@lru_cache
def get_settings() -> Settings:
    return Settings()
