# Users in memory - the database comes back in Video 37
from dataclasses import dataclass

from app.passwords import hash_password, verify_password


@dataclass
class User:
    username: str
    role: str                       # "admin" or "student"
    password_hash: str              # NEVER the password itself


USERS = {
    "nilesh": User("nilesh", "admin", hash_password("admin-pass-123")),
    "asha": User("asha", "student", hash_password("student-pass-123")),
}


def authenticate(username: str, password: str) -> User | None:
    user = USERS.get(username)
    if user is None or not verify_password(password, user.password_hash):
        return None                 # the SAME answer for "no user" and "wrong password"
    return user
