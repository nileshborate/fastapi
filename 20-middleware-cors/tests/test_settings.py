import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.config import Settings, get_settings
from app.main import app
from tests.conftest import ADMIN


def test_settings_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "abc")
    monkeypatch.setenv("DEBUG", "true")                                    # text -> bool
    settings = Settings(_env_file=None)                                    # ignore the .env file here
    assert settings.debug is True
    assert settings.api_key.get_secret_value() == "abc"


def test_missing_api_key_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_secret_is_hidden() -> None:
    settings = Settings(_env_file=None, api_key=SecretStr("super-secret"))
    assert "super-secret" not in str(settings)
    assert str(settings.api_key) == "**********"


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()                                # the same object


def test_override_settings(client: TestClient) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, api_key=SecretStr("x"), environment="prod")
    assert client.get("/").json()["environment"] == "prod"


def test_api_key_comes_from_settings(client: TestClient) -> None:
    body = {"title": "FastAPI Basics", "price": 499}
    assert client.post("/courses", json=body, headers={"X-API-Key": "learn-fastapi-123", "X-Role": "teacher"}).status_code == 401
    assert client.post("/courses", json=body, headers={"X-API-Key": "test-key", "X-Role": "teacher"}).status_code == 201



def test_no_debug_in_prod() -> None:                                       # homework answer (Video 19)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, api_key=SecretStr("x"), environment="prod", debug=True)


def test_admin_config_hides_the_key(client: TestClient) -> None:            # homework answer (Video 19)
    body = client.get("/admin/config", headers=ADMIN).json()
    assert body["max_upload_mb"] == 5
    assert "api_key" not in body and "test-key" not in str(body)
