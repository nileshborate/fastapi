# Create and check JWTs with PyJWT
import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.config import get_settings


class TokenError(Exception):
    pass


def create_access_token(user_id: int, role: str, now: datetime | None = None,
                        name: str | None = None) -> str:
    settings = get_settings()
    now = now or datetime.now(UTC)
    claims = {
        "sub": str(user_id),        # subject: WHO - must be a string
        "role": role,               # our own (private) claim
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,                 # issued at
        "nbf": now,                 # not before
        "exp": now + timedelta(minutes=settings.access_token_minutes),   # expires
        "jti": uuid.uuid4().hex,    # a unique id for THIS token (Video 41: logout)
    }
    if name is not None:
        claims["name"] = name       # homework (Video 38): a claim for display
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],    # a LIST - never trust the header
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "exp", "iat", "iss", "aud"]},
            leeway=10,                              # 10 s for clocks that differ a little
        )
    except jwt.ExpiredSignatureError:
        raise TokenError("Token expired") from None
    except jwt.InvalidTokenError as error:          # signature, issuer, audience, format ...
        raise TokenError(f"Invalid token: {error}") from None
