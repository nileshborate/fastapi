# Run: python -m demos.claims   - what decode() checks, one claim at a time
from datetime import UTC, datetime, timedelta

import jwt

from app.config import get_settings
from app.jwt_tokens import TokenError, create_access_token, decode_access_token

settings = get_settings()
now = datetime.now(UTC)


def check(label: str, token: str) -> None:
    try:
        claims = decode_access_token(token)
        print(f"{label:<22} OK   sub={claims['sub']}")
    except TokenError as error:
        print(f"{label:<22} FAIL {error}")


def forged(**changes: object) -> str:
    claims = {"sub": "2", "role": "student", "iss": settings.jwt_issuer,
              "aud": settings.jwt_audience, "iat": now,
              "exp": now + timedelta(minutes=15)} | changes
    return jwt.encode(claims, settings.jwt_secret, algorithm="HS256")


check("1. fresh token", create_access_token(2, "student"))
check("2. 20 minutes later", create_access_token(2, "student", now - timedelta(minutes=20)))
check("3. 5 s late (leeway)", forged(exp=now - timedelta(seconds=5)))
check("4. wrong issuer", forged(iss="evil-api"))
check("5. wrong audience", forged(aud="another-app"))
check("6. no exp at all", jwt.encode({"sub": "2", "iss": settings.jwt_issuer,
                                      "aud": settings.jwt_audience, "iat": now},
                                     settings.jwt_secret, algorithm="HS256"))
check("7. other secret", jwt.encode({"sub": "2"}, "x" * 32, algorithm="HS256"))
check("8. alg none", jwt.encode({"sub": "2"}, None, algorithm="none"))
