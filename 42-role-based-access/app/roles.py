# Roles, and what each role may do - the RULES live in ONE place
from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


# a role is just a NAME for a set of permissions
PERMISSIONS: dict[Role, set[str]] = {
    Role.STUDENT: {"courses:enroll"},
    Role.TEACHER: {"courses:create", "courses:update"},
    Role.ADMIN: {"courses:create", "courses:update", "courses:delete"},
}


def has_permission(role: str, permission: str) -> bool:
    return permission in PERMISSIONS.get(Role(role), set())
