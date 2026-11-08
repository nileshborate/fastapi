# A short secret: the settings refuse to load
import pytest
from pydantic import ValidationError

from app.config import Settings


def test_short_secret_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "short")
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(_env_file=None)
