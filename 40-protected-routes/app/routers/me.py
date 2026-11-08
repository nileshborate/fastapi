# Everything under /me needs a login - so we protect the WHOLE router at once
from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.deps import DB, CurrentUser, get_current_active_user
from app.models import Course, User
from app.schemas import CourseOut, UserOut

router = APIRouter(prefix="/me", tags=["Me"], dependencies=[Depends(get_current_active_user)])


@router.get("", response_model=UserOut)
async def read_me(user: CurrentUser) -> User:
    return user


@router.get("/courses", response_model=list[CourseOut])
async def my_courses(user: CurrentUser, db: DB) -> list[Course]:
    stmt = select(Course).where(Course.owner_id == user.id).order_by(Course.id)
    return list(await db.scalars(stmt))
