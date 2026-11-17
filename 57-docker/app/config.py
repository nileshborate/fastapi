# Settings - in a container they come from environment variables (ENV, docker run -e, compose)
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    version: str = "1.5.0"
    db_path: str = "coursehub.db"           # the image sets DB_PATH=/data/coursehub.db


@lru_cache
def get_settings() -> Settings:
    return Settings()
