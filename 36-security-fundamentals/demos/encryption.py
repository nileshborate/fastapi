# Run: python -m demos.encryption   - encryption is TWO way: with the key you get it back
from cryptography.fernet import Fernet, InvalidToken

key = Fernet.generate_key()                 # keep it secret - like a house key
box = Fernet(key)

secret = box.encrypt(b"Aadhaar 1234 5678 9012")
print("1. encrypted:", secret[:40].decode(), "...")
print("2. decrypted:", box.decrypt(secret).decode())

try:
    Fernet(Fernet.generate_key()).decrypt(secret)       # the WRONG key
except InvalidToken:
    print("3. wrong key: InvalidToken - nothing to read")
