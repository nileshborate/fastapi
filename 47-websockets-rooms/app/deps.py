# Who is calling? - for HTTP (the Authorization header) AND for WebSockets (a query parameter)
import time
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Query, WebSocket, WebSocketException, status
from fastapi.security import OAuth2PasswordBearer

from app.security import decode_access_token
from app.users import USERS, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def read_token(token: str) -> tuple[User, float] | None:
    """the user and the token's expiry time - or None for any bad token"""
    try:
        claims = decode_access_token(token)
    except jwt.InvalidTokenError:                 # bad signature, expired, garbage, no "sub"
        return None
    user = USERS.get(claims["sub"])
    return (user, claims["exp"]) if user else None


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    found = read_token(token)
    if found is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token",
                            headers={"WWW-Authenticate": "Bearer"})
    return found[0]


async def get_teacher(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "teacher":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Teachers only")
    return user


@dataclass
class WsSession:
    user: User
    expires_at: float                             # the token's "exp" - a Unix time


async def ws_session(websocket: WebSocket,
                     token: Annotated[str | None, Query()] = None) -> WsSession:
    """a browser can't set an Authorization header on a WebSocket -> ?token=..."""
    found = read_token(token) if token else None
    if found is None:                             # raised BEFORE accept: the handshake fails
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION,
                                 reason="invalid or missing token")
    return WsSession(user=found[0], expires_at=found[1])


def seconds_left(session: WsSession) -> float:
    return session.expires_at - time.time()


CurrentUser = Annotated[User, Depends(get_current_user)]
Teacher = Annotated[User, Depends(get_teacher)]
Session = Annotated[WsSession, Depends(ws_session)]
