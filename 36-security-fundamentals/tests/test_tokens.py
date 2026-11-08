# Signed tokens: readable, but not changeable - and they expire
import pytest

from app.tokens import TokenError, create_token, read_token


def test_create_and_read() -> None:
    data = read_token(create_token("asha", "student", now=1000), now=1000)
    assert data == {"sub": "asha", "role": "student", "exp": 1000 + 15 * 60}


def test_changed_token_is_rejected() -> None:
    token = create_token("asha", "student")
    payload, signature = token.split(".")
    with pytest.raises(TokenError, match="Invalid signature"):
        read_token(f"{payload}x.{signature}")
    with pytest.raises(TokenError, match="Malformed"):
        read_token("no-dot-here")


def test_expired() -> None:
    token = create_token("asha", "student", now=1000)
    read_token(token, now=1000 + 15 * 60)                       # the last second: OK
    with pytest.raises(TokenError, match="expired"):
        read_token(token, now=1000 + 15 * 60 + 1)
