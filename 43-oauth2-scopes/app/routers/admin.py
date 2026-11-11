# The whole router needs the scope "users:manage" - Security(...) works on a router too
from typing import Annotated

from fastapi import APIRouter, HTTPException, Security, status
from sqlalchemy import select

from app.deps import DB, get_current_user
from app.models import User
from app.schemas import RoleUpdate, UserOut

router = APIRouter(prefix="/admin", tags=["Admin"],
                   dependencies=[Security(get_current_user, scopes=["users:manage"])])

Admin = Annotated[User, Security(get_current_user, scopes=["users:manage"])]


@router.get("/users", response_model=list[UserOut])
async def list_users(db: DB) -> list[User]:
    return list(await db.scalars(select(User).order_by(User.id)))


@router.patch("/users/{user_id}/role", response_model=UserOut)
async def change_role(user_id: int, data: RoleUpdate, admin: Admin, db: DB) -> User:
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="You can't change your own role")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.role = data.role
    await db.commit()
    await db.refresh(user)
    return user
