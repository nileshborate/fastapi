# Settings: how much to log, and in which format (both can come from env vars)
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service: str = "course-hub"
    log_level: str = "INFO"                 # DEBUG · INFO · WARNING · ERROR
    log_json: bool = True                   # False = plain text, nice on your own laptop


@lru_cache
def get_settings() -> Settings:
    return Settings()
