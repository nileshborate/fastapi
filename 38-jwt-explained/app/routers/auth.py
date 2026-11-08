# Get a JWT, and use it. (Video 39: OAuth2PasswordBearer + the Authorize button)
from typing import Annotated

import jwt
from fastapi import APIRouter, Header, HTTPException, status

from app.config import get_settings
from app.jwt_tokens import TokenError, create_access_token, decode_access_token
from app.schemas import LoginIn, MeOut, TokenOut
from app.users import authenticate, get_user

router = APIRouter(tags=["JWT"])


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail,
                         headers={"WWW-Authenticate": "Bearer"})


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn) -> TokenOut:
    user = authenticate(data.email, data.password)
    if user is None:
        raise unauthorized("Wrong email or password")
    minutes = get_settings().access_token_minutes
    return TokenOut(access_token=create_access_token(user.id, user.role, name=user.name),
                    expires_in=minutes * 60)


@router.get("/me", response_model=MeOut)
def me(authorization: Annotated[str | None, Header()] = None) -> MeOut:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise unauthorized("Not authenticated")
    try:
        claims = decode_access_token(token)
    except TokenError as error:
        raise unauthorized(str(error)) from None
    user = get_user(int(claims["sub"]))
    if user is None:                                # the user was deleted after login
        raise unauthorized("User not found")
    return MeOut(id=user.id, email=user.email, name=claims.get("name", ""), role=user.role,
                 token_expires=claims["exp"])     # the name: straight from the token


# ---------------------------------------------------------------- homework answer (Video 38)
@router.get("/token/info")
def token_info(authorization: Annotated[str | None, Header()] = None) -> dict:
    # DEBUGGING ONLY: this does NOT check the signature, expiry, issuer or audience.
    # Anybody can write any payload - never use these claims to decide who someone is.
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise unauthorized("Not authenticated")
    try:
        claims = jwt.decode(token, options={"verify_signature": False})
        header = jwt.get_unverified_header(token)
    except jwt.DecodeError:
        raise HTTPException(status_code=400, detail="Not a JWT") from None
    return {"header": header, "claims": claims, "verified": False}
