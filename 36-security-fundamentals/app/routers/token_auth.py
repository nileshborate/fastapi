# Login with a TOKEN: the server signs it - and remembers nothing
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import require_admin, token_user
from app.schemas import LoginIn, TokenOut, UserOut
from app.tokens import create_token
from app.users import User, authenticate

router = APIRouter(tags=["Token login"])


@router.post("/token/login", response_model=TokenOut)
def login(data: LoginIn) -> TokenOut:
    user = authenticate(data.username, data.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Wrong username or password")
    return TokenOut(access_token=create_token(user.username, user.role))


@router.get("/token/me", response_model=UserOut)
def me(user: Annotated[User, Depends(token_user)]) -> UserOut:
    return UserOut(username=user.username, role=user.role)


@router.get("/admin/stats")
def admin_stats(admin: Annotated[User, Depends(require_admin)]) -> dict[str, int | str]:
    return {"users": 2, "checked_by": admin.username}
