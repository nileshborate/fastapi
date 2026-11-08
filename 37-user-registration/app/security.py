# Password hashing with pwdlib: Argon2 first - bcrypt only to READ old hashes
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

password_hash = PasswordHash((
    Argon2Hasher(),     # the FIRST hasher makes every new hash
    BcryptHasher(),     # old bcrypt hashes still work - and get upgraded at login
))

# a real hash of a random password: used when the email doesn't exist (same time)
DUMMY_HASH = password_hash.hash("dummy-password-not-used")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> tuple[bool, str | None]:
    """(is it right?, a NEW hash if the old one should be upgraded - else None)"""
    return password_hash.verify_and_update(password, hashed)
