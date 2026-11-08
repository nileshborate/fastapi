# Passwords (Argon2) and TWO kinds of tokens: a short access token, a long refresh token
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import get_settings

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummy-password-not-used")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def _encode(claims: dict) -> str:
    settings = get_settings()
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int, version: int, minutes: int | None = None) -> str:
    now = datetime.now(UTC)
    if minutes is None:
        minutes = get_settings().access_token_minutes      # a demo can pass -1: expired
    return _encode({"sub": str(user_id), "type": "access", "ver": version,
                    "iat": now, "exp": now + timedelta(minutes=minutes)})


def create_refresh_token(user_id: int, days: int | None = None) -> tuple[str, str, datetime]:
    """returns the token, its jti and when it expires"""
    now = datetime.now(UTC)
    if days is None:
        days = get_settings().refresh_token_days
    jti = str(uuid.uuid4())                                 # random and unique
    expires = now + timedelta(days=days)
    token = _encode({"sub": str(user_id), "type": "refresh", "jti": jti,
                     "iat": now, "exp": expires})
    return token, jti, expires


def decode_token(token: str, expected_type: str) -> dict:
    """signature + exp + the right TYPE - raises jwt.InvalidTokenError otherwise"""
    settings = get_settings()
    extra = "jti" if expected_type == "refresh" else "ver"  # each type has its own claim
    claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm],
                        options={"require": ["sub", "exp", "type", extra]})
    if claims["type"] != expected_type:                     # a refresh token is not a key
        raise jwt.InvalidTokenError(f"expected a {expected_type} token")
    return claims
