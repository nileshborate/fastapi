# Everything under /admin: admins only - ONE line protects the whole router
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.deps import DB, CurrentUser, require_roles
from app.models import User
from app.roles import Role
from app.schemas import RoleUpdate, UserOut

router = APIRouter(prefix="/admin", tags=["Admin"],
                   dependencies=[Depends(require_roles(Role.ADMIN))])


@router.get("/users", response_model=list[UserOut])
async def list_users(db: DB) -> list[User]:
    return list(await db.scalars(select(User).order_by(User.id)))


@router.patch("/users/{user_id}/role", response_model=UserOut)
async def change_role(user_id: int, data: RoleUpdate, admin: CurrentUser, db: DB) -> User:
    # the router already checked the role - here we only need WHO the admin is
    if user_id == admin.id:
        # otherwise the last admin could lock everybody out of /admin
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="You can't change your own role")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.role = data.role
    await db.commit()
    await db.refresh(user)
    return user
