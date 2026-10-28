# Settings = values that change between computers and environments (dev, test, prod).
from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Course Hub API"
    environment: Literal["dev", "test", "prod"] = "dev"
    debug: bool = False
    show_docs: bool = True
    api_key: SecretStr                      # required - no default, and hidden when printed


@lru_cache
def get_settings() -> Settings:
    return Settings()                       # reads .env + environment variables ONCE
