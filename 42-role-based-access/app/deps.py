# Who are you? (Video 40)  +  NEW: what may you do? - roles and permissions
from collections.abc import Awaitable, Callable
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.roles import Role, has_permission
from app.security import decode_access_token

DB = Annotated[AsyncSession, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> User:
    try:
        user_id = int(decode_access_token(token)["sub"])
    except (jwt.InvalidTokenError, ValueError):
        raise CREDENTIALS_ERROR from None
    user = await db.get(User, user_id)           # the role comes from HERE - not the token
    if user is None:
        raise CREDENTIALS_ERROR
    return user


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_active_user)]

FORBIDDEN = HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                          detail="Not enough permissions")


def require_roles(*roles: Role) -> Callable[[User], Awaitable[User]]:
    """a dependency FACTORY: you call it, and it gives you a new dependency"""
    async def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise FORBIDDEN
        return user
    return checker


def require_permission(permission: str) -> Callable[[User], Awaitable[User]]:
    async def checker(user: CurrentUser) -> User:
        if not has_permission(user.role, permission):
            raise FORBIDDEN
        return user
    return checker

