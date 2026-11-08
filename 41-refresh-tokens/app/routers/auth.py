# Register, log in, refresh, log out - the whole life of a login
from datetime import UTC, datetime
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import DB, CurrentUser
from app.models import RefreshToken, User
from app.schemas import RefreshIn, TokenPair, UserCreate, UserOut
from app.security import DUMMY_HASH, decode_token, hash_password, verify_password
from app.tokens import issue_pair, revoke_all, rotate

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


@router.post("/token", response_model=TokenPair)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB) -> TokenPair:
    user = await db.scalar(select(User).where(User.email == form.username.lower()))
    if user is None:
        verify_password(form.password, DUMMY_HASH)
    if user is None or not verify_password(form.password, user.password_hash) \
            or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    pair, _ = await issue_pair(db, user)
    await db.commit()                                   # save the refresh token's row
    return pair


@router.post("/token/refresh", response_model=TokenPair)
async def refresh(data: RefreshIn, db: DB) -> TokenPair:
    return await rotate(db, data.refresh_token)          # no password, no access token


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshIn, db: DB) -> Response:
    # log out THIS device: kill its refresh token. Always 204 - logging out never fails.
    try:
        claims = decode_token(data.refresh_token, "refresh")
    except jwt.InvalidTokenError:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    row = await db.scalar(select(RefreshToken).where(RefreshToken.jti == claims["jti"]))
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(UTC)
        await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout/all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(user: CurrentUser, db: DB) -> Response:
    # log out EVERYWHERE: every refresh token dies, and every access token too ("ver")
    await revoke_all(db, user.id)
    user.token_version += 1
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
