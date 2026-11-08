# Run: python -m demos.rs256   - two keys: the PRIVATE key signs, the PUBLIC key only checks
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_pem = private_key.public_key().public_bytes(
    serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)

token = jwt.encode({"sub": "2", "role": "student"}, private_key, algorithm="RS256")
print("1. header:", jwt.get_unverified_header(token))
print("2. checked with the PUBLIC key:", jwt.decode(token, public_pem, algorithms=["RS256"]))

other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
fake = jwt.encode({"sub": "2", "role": "admin"}, other_key, algorithm="RS256")
try:
    jwt.decode(fake, public_pem, algorithms=["RS256"])     # signed by ANOTHER private key
except jwt.InvalidSignatureError as error:
    print("3. a token from another private key:", error)

print("4. public key:", public_pem.decode().splitlines()[0], "...  share it freely")
