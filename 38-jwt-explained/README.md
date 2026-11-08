# 38 – JWT Explained

**Video 38** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

What a **JSON Web Token** really is – header, payload, signature – the standard **claims**,
expiry, and signing keys (HS256 and RS256), with **PyJWT**. No database today: two users live
in `app/users.py` (Argon2 hashes, Video 37).

## Run it
```bash
cd 38-jwt-explained
pip install -r requirements.txt
cp .env.example .env
python -m demos.anatomy        # three parts · base64 · change the role -> signature fails
python -m demos.claims         # expired · leeway · iss · aud · missing exp · alg none
python -m demos.rs256          # private key signs, public key checks
fastapi dev app/main.py        # POST /login -> a JWT ·  GET /me  with  Authorization: Bearer
pytest                         # 13 passed
```
Users: `nilesh@example.com` / `admin-pass-123` (admin) · `asha@example.com` / `blue-river-42` (student)

## Project
```
app/
  config.py        JWT_SECRET (min 32 chars) · JWT_ALGORITHM · ACCESS_TOKEN_MINUTES · ISSUER · AUDIENCE
  jwt_tokens.py    create_access_token · decode_access_token (algorithms=[...], iss, aud, require, leeway)
  users.py         two users, Argon2 hashes
  routers/auth.py  POST /login -> {access_token, token_type, expires_in} · GET /me
demos/   anatomy.py · claims.py · rs256.py
tests/   test_jwt_tokens · test_api · test_config
```

## A JWT
```
eyJhbGciOi...  .  eyJzdWIiOi...  .  SBRBZjZ5-9j...
   header           payload          signature = HMAC-SHA256(secret, header + "." + payload)
{"alg":"HS256",  {"sub":"2", "role":"student", "iss":..., "aud":..., "iat":..., "exp":..., "jti":...}
 "typ":"JWT"}
```
Base64url is **not** encryption – everybody can read the payload. The signature only makes sure
nobody **changed** it.

## The claims
| Claim | Means | Checked by `jwt.decode` |
|---|---|---|
| `sub` | subject – who (a **string**) | must be a string |
| `exp` | expires at | `ExpiredSignatureError` (with `leeway`) |
| `iat` | issued at | – |
| `nbf` | not before | `ImmatureSignatureError` |
| `iss` | issuer – who made it | `issuer=` → `InvalidIssuerError` |
| `aud` | audience – who it is for | `audience=` → `InvalidAudienceError` |
| `jti` | a unique id for this token | – (used for logout in Video 41) |
| `role` | our own claim | – |

## HS256 vs RS256
| | HS256 | RS256 |
|---|---|---|
| Keys | ONE secret – signs and checks | a private key signs, a public key checks |
| Use | one API makes and checks its tokens | many services check, only one makes them |

## Rules
- `algorithms=["HS256"]` – a **list** you choose. Never trust the `alg` in the header (`alg: none`!).
- A long random secret (≥ 32 bytes for HS256), from `.env` – never in the code.
- Short-lived access tokens (15 minutes), `require` the claims you rely on, `leeway` of a few seconds.
- No secrets in the payload: no passwords, no Aadhaar numbers.

## Interview questions
1. **What are the three parts of a JWT?** Header (algorithm and type), payload (the claims), signature (over header and payload, with the key) – base64url, joined with dots. The payload is readable by anybody; the signature only proves it wasn't changed.
2. **Which claims do you check, and how does a JWT expire?** `exp` (with a little leeway), plus `iss` and `aud`, and require the claims you need. Expiry is just the `exp` claim: after that time `decode` refuses the token – the server stores nothing.
3. **HS256 or RS256?** HS256 uses one shared secret to sign and check – simple, for one API. RS256 signs with a private key and checks with a public key – many services can verify tokens without being able to create them.

## Homework
1. Add a `name` claim to the token and show it in `GET /me` – without looking up the user.
2. `GET /token/info` – decode the token **without** checking it (`options={"verify_signature": False}`) and return header + claims. Explain in a comment why you must **never** use that for login.
3. Tests: a token signed with RS256 by another key is rejected by `decode_access_token`.

Answer at the start of Video 39 (Login with OAuth2 Password Flow).

## Homework answer (shown at the start of Video 39)
```python
# jwt_tokens.py - an optional "name" claim
if name is not None:
    claims["name"] = name
# routers/auth.py - GET /me takes the name straight from the token (no lookup)
name=claims.get("name", "")

# GET /token/info - DEBUGGING ONLY
claims = jwt.decode(token, options={"verify_signature": False})
# no signature, no exp, no iss/aud check: anybody can write any payload.
# Never use these claims to decide WHO someone is - that's what decode_access_token is for.
```
`tests/test_homework38.py`: a fake admin token shows up in `/token/info` (`"verified": false`) but
`/me` refuses it (401). An RS256 token from another key → "The specified alg value is not allowed"
(we only accept HS256). `pytest` → **16 passed**.
