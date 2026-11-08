# The token functions - no HTTP
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config import get_settings
from app.jwt_tokens import TokenError, create_access_token, decode_access_token

NOW = datetime.now(UTC)


def test_round_trip() -> None:
    claims = decode_access_token(create_access_token(2, "student"))
    assert claims["sub"] == "2" and claims["role"] == "student"
    assert claims["exp"] - claims["iat"] == 15 * 60
    assert claims["iss"] == "course-hub-api" and claims["aud"] == "course-hub-app"


def test_three_parts_and_readable_header() -> None:
    token = create_access_token(2, "student")
    assert token.count(".") == 2
    assert jwt.get_unverified_header(token) == {"alg": "HS256", "typ": "JWT"}


def test_every_token_has_its_own_jti() -> None:
    first, second = (decode_access_token(create_access_token(2, "student")) for _ in range(2))
    assert first["jti"] != second["jti"]


def test_expired_and_leeway() -> None:
    with pytest.raises(TokenError, match="Token expired"):
        decode_access_token(create_access_token(2, "student", NOW - timedelta(minutes=16)))
    late = create_access_token(2, "student", NOW - timedelta(minutes=15, seconds=5))
    assert decode_access_token(late)["sub"] == "2"              # 5 s late: inside leeway


@pytest.mark.parametrize(("token", "message"), [
    (jwt.encode({"sub": "2"}, "y" * 40, algorithm="HS256"), "Signature verification failed"),
    (jwt.encode({"sub": "2"}, None, algorithm="none"), "alg value is not allowed"),
    ("not.a.jwt", "Invalid"),
])
def test_rejected(token: str, message: str) -> None:
    with pytest.raises(TokenError, match=message):
        decode_access_token(token)


def test_wrong_audience() -> None:
    settings = get_settings()
    token = jwt.encode({"sub": "2", "iss": settings.jwt_issuer, "aud": "another-app",
                        "iat": NOW, "exp": NOW + timedelta(minutes=5)},
                       settings.jwt_secret, algorithm="HS256")
    with pytest.raises(TokenError, match="Audience doesn't match"):
        decode_access_token(token)
