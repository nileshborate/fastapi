# Run: python -m demos.hashing   - what a hash is, and why a FAST hash is bad for passwords
import hashlib
import time

from app.passwords import hash_password, verify_password

print("1.", hashlib.sha256(b"admin-pass-123").hexdigest()[:32], "...")
print("2.", hashlib.sha256(b"admin-pass-123").hexdigest()[:32], "...  same input = same hash")
print("3.", hashlib.sha256(b"admin-pass-124").hexdigest()[:32], "...  one letter = new hash")

start, count = time.perf_counter(), 0
while time.perf_counter() - start < 1:
    hashlib.sha256(f"guess-{count}".encode()).digest()
    count += 1
print(f"4. sha256: {count:,} guesses per second  - FAST = bad for passwords")

start = time.perf_counter()
stored = hash_password("admin-pass-123")
print(f"5. pbkdf2: {time.perf_counter() - start:.2f} s for ONE hash  - slow on purpose")
print("6. stored:", stored[:52], "...")
print("7. again: ", hash_password("admin-pass-123")[:52], "...  new salt = new hash")
print("8. verify right:", verify_password("admin-pass-123", stored),
      "| wrong:", verify_password("admin-pass-999", stored))
