# The dependencies that protect our routes (Video 40) - now with "type" and "ver" checks
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.security import decode_token

DB = Annotated[AsyncSession, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> User:
    try:
        claims = decode_token(token, "access")          # a refresh token is refused here
        user_id = int(claims["sub"])
        version = int(claims["ver"])
    except (jwt.InvalidTokenError, ValueError):
        raise CREDENTIALS_ERROR from None
    user = await db.get(User, user_id)
    if user is None:
        raise CREDENTIALS_ERROR
    if version != user.token_version:                   # "log out everywhere" happened
        raise CREDENTIALS_ERROR
    return user


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_active_user)]
