# Run: python -m demos.signing   - a signature: everybody can READ it, nobody can CHANGE it
import base64
import json

from app.tokens import TokenError, create_token, read_token

token = create_token("asha", "student")
print("1. token:", token[:60], "...")
print("2. read: ", read_token(token))

payload, signature = token.split(".")
data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
data["role"] = "admin"                                      # try to become admin ...
fake = base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
try:
    read_token(f"{fake}.{signature}")                       # ... with the OLD signature
except TokenError as error:
    print("3. changed role:", error)

try:
    read_token(token, now=data["exp"] + 1)                  # one second too late
except TokenError as error:
    print("4. one second later:", error)
