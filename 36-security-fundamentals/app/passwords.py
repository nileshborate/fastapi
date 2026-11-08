# Password HASHING - one way. We store the hash, never the password.
# (Python's standard library only - Video 37 uses Argon2, the best choice today)
import hashlib
import hmac
import secrets

ITERATIONS = 600_000                # slow on purpose: 600 000 rounds (OWASP for PBKDF2)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)                  # a NEW random salt for every password
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    _, iterations, salt_hex, digest_hex = stored.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex),
                                 int(iterations))
    return hmac.compare_digest(digest.hex(), digest_hex)    # constant time: no timing leak
