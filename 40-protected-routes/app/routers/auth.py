# Register + log in (Video 39) - the doors to get a token
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.deps import DB
from app.models import User
from app.schemas import Token, UserCreate, UserOut
from app.security import DUMMY_HASH, create_access_token, hash_password, verify_password

router = APIRouter(tags=["Auth"])


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
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


@router.post("/token", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB) -> Token:
    user = await db.scalar(select(User).where(User.email == form.username.lower()))
    if user is None:
        verify_password(form.password, DUMMY_HASH)
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    minutes = get_settings().access_token_minutes
    return Token(access_token=create_access_token(user.id), expires_in=minutes * 60)
