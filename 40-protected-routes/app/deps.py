# The dependencies that protect our routes - written ONCE, used everywhere
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.security import decode_access_token

DB = Annotated[AsyncSession, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# auto_error=False: no token -> None instead of a 401 (for routes that work for everybody)
oauth2_optional = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,           # 401: we don't know who you are
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def user_from_token(token: str, db: AsyncSession) -> User:
    """token -> claims -> user id -> the user from the database. Anything wrong: 401."""
    try:
        claims = decode_access_token(token)             # signature + exp checked here
        user_id = int(claims["sub"])                    # "sub" must be a number
    except (jwt.InvalidTokenError, ValueError):
        raise CREDENTIALS_ERROR from None
    user = await db.get(User, user_id)
    if user is None:                                    # deleted after the login
        raise CREDENTIALS_ERROR
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> User:
    return await user_from_token(token, db)


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_active:                              # we KNOW who you are - but no
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


async def get_optional_user(token: Annotated[str | None, Depends(oauth2_optional)],
                            db: DB) -> User | None:
    if token is None:
        return None                                     # a guest - that's fine here
    return await user_from_token(token, db)             # a token? then it must be valid


# use these in the endpoints - one short name each
CurrentUser = Annotated[User, Depends(get_current_active_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
