# A tiny SIGNED token - to see the idea. Real projects use JWT (Video 38).
# token = base64(payload) + "." + base64(HMAC-SHA256(secret, payload))
import base64
import hashlib
import hmac
import json
import time

from app.config import get_settings


class TokenError(Exception):
    pass


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(payload: str) -> str:
    key = get_settings().secret_key.encode()
    return _b64(hmac.new(key, payload.encode(), hashlib.sha256).digest())


def create_token(username: str, role: str, now: float | None = None) -> str:
    now = time.time() if now is None else now
    exp = int(now) + get_settings().token_minutes * 60
    payload = _b64(json.dumps({"sub": username, "role": role, "exp": exp}).encode())
    return f"{payload}.{_sign(payload)}"


def read_token(token: str, now: float | None = None) -> dict:
    try:
        payload, signature = token.split(".")
    except ValueError:
        raise TokenError("Malformed token") from None
    if not hmac.compare_digest(signature, _sign(payload)):
        raise TokenError("Invalid signature")       # someone changed the payload
    data = json.loads(_unb64(payload))
    if (time.time() if now is None else now) > data["exp"]:
        raise TokenError("Token expired")
    return data
