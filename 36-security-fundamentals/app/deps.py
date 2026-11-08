# Who are you? (authentication)  ·  What may you do? (authorization)
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status

from app.sessions import SESSIONS
from app.tokens import TokenError, read_token
from app.users import USERS, User

NOT_LOGGED_IN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,         # 401: we don't know who you are
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def session_user(session_id: Annotated[str | None, Cookie()] = None) -> User:
    username = SESSIONS.get(session_id or "")       # the server REMEMBERS the session
    if username is None:
        raise NOT_LOGGED_IN
    return USERS[username]


def token_user(authorization: Annotated[str | None, Header()] = None) -> User:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise NOT_LOGGED_IN
    try:
        data = read_token(token)                    # the server remembers NOTHING
    except TokenError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error),
                            headers={"WWW-Authenticate": "Bearer"}) from None
    return USERS[data["sub"]]


def require_admin(user: Annotated[User, Depends(token_user)]) -> User:
    if user.role != "admin":                        # 403: we know you - but no
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    return user
