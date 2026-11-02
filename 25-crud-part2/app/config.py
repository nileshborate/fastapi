# Settings = values that change between computers and environments (dev, test, prod).
from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Course Hub API"
    environment: Literal["dev", "test", "prod"] = "dev"
    debug: bool = False
    show_docs: bool = True
    api_key: SecretStr                      # required - no default, and hidden when printed
    database_url: str = "sqlite:///./coursehub.db"            # Video 23: now we really use it
    db_echo: bool = False                                      # True: print every SQL statement
    max_upload_mb: int = Field(default=5, ge=1, le=50)         # homework answer (Video 19)
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]   # CORS (Video 20)
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]       # homework answer (Video 20)
    log_file: Path = Path("app.log")                            # NEW: background tasks write here
    email_delay_seconds: float = 3.0                            # NEW: our "slow mail server"
    load_seed_data: bool = True                                 # NEW: lifespan loads the courses
    seed_file: Path = Path("data/courses.json")

    @model_validator(mode="after")
    def no_debug_in_prod(self) -> Self:                        # homework answer (Video 19)
        if self.environment == "prod" and self.debug:
            raise ValueError("debug must be False in prod")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()                       # reads .env + environment variables ONCE
