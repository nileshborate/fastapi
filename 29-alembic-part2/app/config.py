# Settings: read from .env (or real environment variables)
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./school.db"
    db_echo: bool = False                        # True: print every SQL statement


@lru_cache
def get_settings() -> Settings:
    return Settings()
