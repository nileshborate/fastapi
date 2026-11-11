from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.ratelimit import client_ip
from app.security import decode_access_token

DB = Annotated[AsyncSession, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> User:
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail="Could not validate credentials",
                          headers={"WWW-Authenticate": "Bearer"})
    try:
        user_id = int(decode_access_token(token)["sub"])
    except (jwt.InvalidTokenError, ValueError):
        raise error from None
    user = await db.get(User, user_id)
    if user is None:
        raise error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def limit_writes(request: Request, user: CurrentUser) -> None:
    """at most N course writes per minute per USER - logged in, so we know who it is"""
    request.app.state.write_limiter.check(f"user:{user.id}")


async def limit_ip(request: Request) -> None:
    """for routes without a login: per IP address"""
    request.app.state.ip_limiter.check(f"ip:{client_ip(request)}:{request.url.path}")
