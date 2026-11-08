# Run: python -m demos.anatomy   - a JWT is three base64url parts: header.payload.signature
import base64
import json

from app.jwt_tokens import TokenError, create_access_token, decode_access_token


def b64decode(part: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))


token = create_access_token(user_id=2, role="student")
header, payload, signature = token.split(".")

print("1. token:    ", token[:56], "...")
print("2. parts:    ", len(token.split(".")), "- separated by dots")
print("3. header:   ", b64decode(header))
print("4. payload:  ", b64decode(payload))
print("5. signature:", signature[:30], "...  (HMAC-SHA256 of header.payload)")
print("6. anyone can read it - base64 is NOT encryption")

data = b64decode(payload) | {"role": "admin"}                   # try to become admin
fake_payload = base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
try:
    decode_access_token(f"{header}.{fake_payload}.{signature}")
except TokenError as error:
    print("7. role -> admin, old signature:", error)
