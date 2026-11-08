# OAuth2 password flow: a FORM with username + password  ->  {"access_token", "token_type"}
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import Token
from app.security import DUMMY_HASH, create_access_token, verify_password

router = APIRouter(tags=["Auth"])

DB = Annotated[AsyncSession, Depends(get_db)]


@router.post("/token", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB) -> Token:
    # OAuth2 calls the field "username" - our users log in with their EMAIL
    user = await db.scalar(select(User).where(User.email == form.username.lower()))
    if user is None:
        verify_password(form.password, DUMMY_HASH)          # same time (Video 37)
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id))
