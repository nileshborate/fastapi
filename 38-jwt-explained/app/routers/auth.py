# Get a JWT, and use it. (Video 39: OAuth2PasswordBearer + the Authorize button)
from typing import Annotated

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
    return TokenOut(access_token=create_access_token(user.id, user.role),
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
    return MeOut(id=user.id, email=user.email, role=user.role, token_expires=claims["exp"])
