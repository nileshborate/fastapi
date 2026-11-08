# Users in memory - the database comes back in Video 37
from dataclasses import dataclass

from fastapi import HTTPException, status

from app import lockout

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


# ---------------------------------------------------------------- homework answer (Video 36)
def check_login(username: str, password: str) -> User:
    """authenticate() + the lockout: 429 while blocked, 401 for a wrong password"""
    if lockout.is_blocked(username):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Too many wrong passwords - try again later")
    user = authenticate(username, password)
    if user is None:
        lockout.record_failure(username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Wrong username or password")
    lockout.record_success(username)
    return user
