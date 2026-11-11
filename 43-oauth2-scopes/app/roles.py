# Roles (Video 42) - and which SCOPES each role may ever get
from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


# every scope our API knows - the text is what Swagger shows next to the checkbox
SCOPES: dict[str, str] = {
    "me": "Read your own profile",
    "courses:read": "Read courses",
    "courses:write": "Create courses",
    "courses:delete": "Delete courses",                 # homework 43 - admins only
    "users:manage": "List users and change their roles",
}

# the MOST a user with this role can get - a token may carry fewer
ROLE_SCOPES: dict[Role, set[str]] = {
    Role.STUDENT: {"me", "courses:read"},
    Role.TEACHER: {"me", "courses:read", "courses:write"},
    Role.ADMIN: set(SCOPES),                          # so admins get courses:delete too
}


def grant_scopes(role: str, requested: list[str]) -> list[str]:
    """nothing requested -> everything the role allows; else: requested AND allowed"""
    allowed = ROLE_SCOPES[Role(role)]
    if not requested:
        return sorted(allowed)
    return sorted(set(requested) & allowed)
