# Register, and log in WITH scopes: the client asks, the server decides
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import DB, Claims, Me
from app.models import User
from app.roles import SCOPES, grant_scopes
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
    # form.scopes: the form field "scope" ("me courses:read"), split at the spaces
    unknown = [scope for scope in form.scopes if scope not in SCOPES]
    if unknown:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Unknown scope: {' '.join(unknown)}")
    user = await db.scalar(select(User).where(User.email == form.username.lower()))
    if user is None:
        verify_password(form.password, DUMMY_HASH)
    if user is None or not verify_password(form.password, user.password_hash) \
            or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    scopes = grant_scopes(user.role, form.scopes)       # never more than the role allows
    return Token(access_token=create_access_token(user.id, scopes), scope=" ".join(scopes))


@router.get("/me", response_model=UserOut)
async def read_me(user: Me) -> User:
    return user


@router.get("/me/token")
async def my_token(user: Me, claims: Claims) -> dict:
    # homework 43: Me checks the token first - then we just show its claims
    expires = datetime.fromtimestamp(claims["exp"], UTC)
    seconds_left = int((expires - datetime.now(UTC)).total_seconds())
    return {"user_id": user.id, "scopes": claims.get("scope", "").split(),
            "expires_at": expires.isoformat(), "expires_in": seconds_left}
