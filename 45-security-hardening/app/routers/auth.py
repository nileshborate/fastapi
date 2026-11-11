# Register and log in - the login is rate limited (brute force!)
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import DB, CurrentUser, limit_ip
from app.models import User
from app.ratelimit import client_ip
from app.schemas import Token, UserCreate, UserOut
from app.security import DUMMY_HASH, create_access_token, hash_password, verify_password

router = APIRouter(tags=["Auth"])


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(limit_ip)])
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
async def login(request: Request, form: Annotated[OAuth2PasswordRequestForm, Depends()],
                db: DB) -> Token:
    # FIRST the limit - before the slow Argon2 check: 5 tries / minute / IP + email
    key = f"login:{client_ip(request)}:{form.username.lower()}"
    request.app.state.login_limiter.check(key)
    user = await db.scalar(select(User).where(User.email == form.username.lower()))
    if user is None:
        verify_password(form.password, DUMMY_HASH)
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
async def read_me(user: CurrentUser) -> User:
    return user
