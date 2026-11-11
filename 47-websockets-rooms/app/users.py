# The users of this small project live in memory, so we can focus on WebSockets.
# (A real app: the users table from Videos 37-44.)  Every password: blue-river-42
from dataclasses import dataclass

from app.security import hash_password

PASSWORD = "blue-river-42"


@dataclass(frozen=True)
class User:
    username: str
    full_name: str
    role: str                         # "student" or "teacher"
    rooms: frozenset[str]             # the course rooms this user may join
    password_hash: str


def _user(username: str, full_name: str, role: str, rooms: set[str]) -> User:
    return User(username, full_name, role, frozenset(rooms), hash_password(PASSWORD))


USERS: dict[str, User] = {user.username: user for user in [
    _user("asha", "Asha Rao", "student", {"python", "sql"}),
    _user("ravi", "Ravi Kumar", "student", {"python"}),
    _user("meera", "Meera Shah", "student", {"sql"}),
    _user("nilesh", "Nilesh Borate", "teacher", {"python", "sql", "fastapi"}),
]}
