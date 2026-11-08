from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut
from app.security import decode_access_token, hash_password

router = APIRouter(prefix="/users", tags=["Users"])

DB = Annotated[AsyncSession, Depends(get_db)]

# reads "Authorization: Bearer <token>" - and tells Swagger WHERE to get a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: DB) -> User:
    user = User(email=data.email, full_name=data.full_name,
                password_hash=hash_password(data.password))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Email already registered") from None
    await db.refresh(user)
    return user


@router.get("/me", response_model=UserOut)
async def read_me(token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> User:
    # Video 40 moves these lines into a reusable get_current_user dependency
    try:
        user_id = int(decode_access_token(token)["sub"])
    except jwt.InvalidTokenError:
        user_id = None
    user = await db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials",
                            headers={"WWW-Authenticate": "Bearer"})
    return user
