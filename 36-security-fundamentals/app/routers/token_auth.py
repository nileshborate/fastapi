# Login with a TOKEN: the server signs it - and remembers nothing
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import require_admin, token_user
from app.passwords import hash_password, verify_password
from app.schemas import LoginIn, PasswordChange, TokenOut, UserOut
from app.tokens import create_token
from app.users import User, check_login

router = APIRouter(tags=["Token login"])


@router.post("/token/login", response_model=TokenOut)
def login(data: LoginIn) -> TokenOut:
    user = check_login(data.username, data.password)       # homework: + lockout (429)
    return TokenOut(access_token=create_token(user.username, user.role))


@router.get("/token/me", response_model=UserOut)
def me(user: Annotated[User, Depends(token_user)]) -> UserOut:
    return UserOut(username=user.username, role=user.role)


@router.get("/admin/stats")
def admin_stats(admin: Annotated[User, Depends(require_admin)]) -> dict[str, int | str]:
    return {"users": 2, "checked_by": admin.username}


# ---------------------------------------------------------------- homework answer (Video 36)
@router.post("/token/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(data: PasswordChange, user: Annotated[User, Depends(token_user)]) -> None:
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password")
    user.password_hash = hash_password(data.new_password)     # store the NEW hash
