# Run: python -m demos.argon2_demo   - Argon2: what the hash says, how slow it is, upgrades
import time

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.security import hash_password, verify_password

start = time.perf_counter()
stored = hash_password("my-secret-pass")
print(f"1. argon2: {time.perf_counter() - start:.3f} s")
print("2.", stored)
print("   ", " | ".join(stored.split("$")[1:4]))           # algorithm | version | cost
print("3. right:", verify_password("my-secret-pass", stored))
print("4. wrong:", verify_password("my-secret-pazz", stored))

old = PasswordHash((BcryptHasher(),)).hash("my-secret-pass")  # a hash from an OLD system
print("5. bcrypt:", old)
ok, new_hash = verify_password("my-secret-pass", old)
print("6. upgrade:", ok, "->", new_hash[:30], "...")
try:
    PasswordHash((BcryptHasher(),)).hash("x" * 100)        # bcrypt: max 72 bytes
except ValueError as error:
    print("7. bcrypt, 100 chars:", error)
print("8. argon2, 100 chars:", hash_password("x" * 100)[:30], "...")
