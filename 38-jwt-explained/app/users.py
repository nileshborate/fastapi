# Two users in memory - Video 37 showed the real users table
from dataclasses import dataclass

from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()          # Argon2


@dataclass
class User:
    id: int
    email: str
    name: str                       # homework (Video 38): goes into the token
    role: str
    password_hash: str


USERS = {
    "nilesh@example.com": User(1, "nilesh@example.com", "Nilesh", "admin",
                               password_hash.hash("admin-pass-123")),
    "asha@example.com": User(2, "asha@example.com", "Asha", "student",
                             password_hash.hash("blue-river-42")),
}


def authenticate(email: str, password: str) -> User | None:
    user = USERS.get(email.lower())
    if user is None or not password_hash.verify(password, user.password_hash):
        return None
    return user


def get_user(user_id: int) -> User | None:
    return next((u for u in USERS.values() if u.id == user_id), None)
