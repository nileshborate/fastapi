# Login with a SESSION: the server keeps a list - the browser keeps only a random id
import secrets
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status

from app.config import get_settings
from app.deps import session_user
from app.schemas import LoginIn, UserOut
from app.sessions import SESSIONS
from app.users import User, check_login

router = APIRouter(prefix="/session", tags=["Session login"])


@router.post("/login", response_model=UserOut)
def login(data: LoginIn, response: Response) -> UserOut:
    user = check_login(data.username, data.password)       # homework: + lockout (429)
    session_id = secrets.token_urlsafe(32)              # random - impossible to guess
    SESSIONS[session_id] = user.username                # the server remembers it
    settings = get_settings()
    response.set_cookie("session_id", session_id, httponly=True, samesite="lax",
                        secure=settings.cookie_secure, max_age=settings.session_minutes * 60)
    return UserOut(username=user.username, role=user.role)


@router.get("/me", response_model=UserOut)
def me(user: Annotated[User, Depends(session_user)]) -> UserOut:
    return UserOut(username=user.username, role=user.role)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, session_id: Annotated[str | None, Cookie()] = None) -> None:
    SESSIONS.pop(session_id or "", None)                # gone on the server = logged out NOW
    response.delete_cookie("session_id")
