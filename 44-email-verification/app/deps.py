from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.mailer import Mailer, get_mailer
from app.models import User
from app.security import decode_access_token

DB = Annotated[AsyncSession, Depends(get_db)]
MailerDep = Annotated[Mailer, Depends(get_mailer)]      # tests swap it with overrides

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
    if user is None or not user.is_active:
        raise error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
