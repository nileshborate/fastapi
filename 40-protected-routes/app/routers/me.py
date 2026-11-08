# Everything under /me needs a login - so we protect the WHOLE router at once
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.deps import DB, CurrentUser, get_current_active_user
from app.models import Course, User
from app.schemas import CourseOut, MeUpdate, UserOut

router = APIRouter(prefix="/me", tags=["Me"], dependencies=[Depends(get_current_active_user)])


@router.get("", response_model=UserOut)
async def read_me(user: CurrentUser) -> User:
    return user


@router.patch("", response_model=UserOut)
async def update_me(data: MeUpdate, user: CurrentUser, db: DB) -> User:
    # homework 40: the user comes from the token - you can only ever change YOURSELF
    user.full_name = data.full_name
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/courses", response_model=list[CourseOut])
async def my_courses(user: CurrentUser, db: DB) -> list[Course]:
    stmt = select(Course).where(Course.owner_id == user.id).order_by(Course.id)
    return list(await db.scalars(stmt))


@router.get("/courses/{course_id}", response_model=CourseOut)
async def my_course(course_id: int, user: CurrentUser, db: DB) -> Course:
    # homework 40: somebody else's course -> 404, NOT 403.
    # 403 would tell an attacker "course 7 exists, it's just not yours" - so they could
    # count the courses or guess ids. Under /me, a course that isn't yours doesn't exist.
    stmt = select(Course).where(Course.id == course_id, Course.owner_id == user.id)
    course = await db.scalar(stmt)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course
