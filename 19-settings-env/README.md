# 19 – Settings and Environment Variables

**FastAPI Mastery: Zero to Production** – Video 19 · Nilesh Technology

Secrets and environment-specific values don't belong in the code. We move them into a `.env` file and read them with **pydantic-settings**.

## What's new
```
19-settings-env/
├── .env.example        # committed: the list of settings, with placeholder values
├── .env                # NOT committed (.gitignore): your real values
├── .gitignore
└── app/
    ├── config.py       # NEW: Settings(BaseSettings) + get_settings() with @lru_cache
    ├── dependencies.py # verify_api_key reads settings.api_key · CourseFilter · request_timer
    └── main.py         # title + docs from settings · app-wide request_timer
```

## Run it
```bash
cd 19-settings-env
pip install -r requirements.txt          # adds pydantic-settings
cp .env.example .env                     # Windows: copy .env.example .env  - then set API_KEY
fastapi dev app/main.py
pytest -v                                # 20 passed
```

## How a value is found (first match wins)
1. Real environment variables (`API_KEY=... fastapi dev ...`, or set by your server)
2. The `.env` file
3. The default value in the class (no default → required → startup error)

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    debug: bool = False          # "true", "1", "yes" -> True
    api_key: SecretStr           # required, shown as '**********'

@lru_cache
def get_settings() -> Settings:  # read once, reuse
    return Settings()
```

## Interview questions
1. **How do you manage configuration in FastAPI?** A `Settings` class that inherits from `BaseSettings` (pydantic-settings). Each field reads an environment variable with the same name (case-insensitive) or a `.env` file, converts and validates the type, and fails at startup if a required value is missing. Provide it with a cached `get_settings()` dependency.
2. **Why `@lru_cache` on `get_settings`?** Reading files and environment variables on every request is wasteful. `lru_cache` creates the `Settings` object once and returns the same object afterwards. In tests you can override it with `app.dependency_overrides[get_settings]`.
3. **How do you keep secrets safe?** Never commit them: `.env` goes in `.gitignore`, and only `.env.example` is committed. Use `SecretStr` so values don't appear in logs or `print`, and in production set real environment variables (or a secrets manager) instead of a file.

## Homework
1. Add `database_url: str = "sqlite:///./coursehub.db"` and `max_upload_mb: int` (1–50, default 5) to `Settings`, and to `.env.example`.
2. Add `GET /admin/config` (admin router) that returns `app_name`, `environment`, `debug` and `max_upload_mb` – **never** the API key.
3. Add a `model_validator`: if `environment == "prod"`, `debug` must be `False`.
4. Tests for 2 and 3.

Answer at the start of Video 20.
