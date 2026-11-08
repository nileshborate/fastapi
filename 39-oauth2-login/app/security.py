# Passwords (Argon2, Video 37) and access tokens (JWT, Video 38) - in one place
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


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    claims = {"sub": str(user_id), "iat": now,
              "exp": now + timedelta(minutes=settings.access_token_minutes)}
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """raises jwt.InvalidTokenError if the token is wrong or expired"""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm],
                      options={"require": ["sub", "exp"]})
