# Passwords (Argon2) and access tokens (JWT) - from Videos 37 to 39
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


def create_access_token(user_id: int, minutes: int | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    if minutes is None:
        minutes = settings.access_token_minutes        # a demo can pass -1: already expired
    claims = {"sub": str(user_id), "iat": now, "exp": now + timedelta(minutes=minutes)}
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """raises jwt.InvalidTokenError (or a subclass) if the token is wrong or expired"""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm],
                      options={"require": ["sub", "exp"]})
