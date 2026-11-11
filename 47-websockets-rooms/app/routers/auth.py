# Log in -> a JWT (the same /token as Video 39)
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas import Token
from app.security import DUMMY_HASH, create_access_token, verify_password
from app.users import USERS

router = APIRouter(tags=["Auth"])


@router.post("/token", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = USERS.get(form.username.lower())
    hashed = user.password_hash if user else DUMMY_HASH       # same time for unknown users
    if not verify_password(form.password, hashed) or user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    return Token(access_token=create_access_token(user.username))
