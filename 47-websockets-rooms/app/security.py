# Passwords (Argon2) and access tokens (JWT) - the same ideas as Videos 37-41
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


def create_access_token(username: str, lifetime: timedelta | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    lifetime = lifetime or timedelta(minutes=settings.access_token_minutes)
    claims = {"sub": username, "iat": now, "exp": now + lifetime}
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm],
                      options={"require": ["sub", "exp"]})
