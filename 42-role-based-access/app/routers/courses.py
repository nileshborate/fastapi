# Courses: anybody reads, teachers create, the OWNER (or an admin) changes, admins delete
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import DB, CurrentUser, require_permission
from app.models import Course, Enrollment, User
from app.roles import Role
from app.schemas import CourseIn, CourseOut, CourseUpdate, UserOut

router = APIRouter(prefix="/courses", tags=["Courses"])

CanCreate = Annotated[User, Depends(require_permission("courses:create"))]
CanUpdate = Annotated[User, Depends(require_permission("courses:update"))]
CanEnroll = Annotated[User, Depends(require_permission("courses:enroll"))]


async def get_course(db: DB, course_id: int) -> Course:
    course = await db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.get("", response_model=list[CourseOut])
async def list_courses(db: DB) -> list[Course]:
    return list(await db.scalars(select(Course).order_by(Course.id)))      # public


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(data: CourseIn, user: CanCreate, db: DB) -> Course:
    course = Course(**data.model_dump(), teacher_id=user.id)
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


@router.patch("/{course_id}", response_model=CourseOut)
async def update_course(course_id: int, data: CourseUpdate, user: CanUpdate, db: DB) -> Course:
    course = await get_course(db, course_id)
    # the ROLE says "teachers may update courses" - the OWNER rule says "only YOUR course"
    if user.role != Role.ADMIN and course.teacher_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only the course's teacher or an admin can change it")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    await db.commit()
    await db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_permission("courses:delete"))])
async def delete_course(course_id: int, db: DB) -> Response:
    course = await get_course(db, course_id)                     # only the check - no user
    await db.delete(course)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{course_id}/students", response_model=list[UserOut])
async def course_students(course_id: int, user: CurrentUser, db: DB) -> list[User]:
    # homework 42: the course's OWN teacher or an admin - the same owner rule as PATCH
    course = await get_course(db, course_id)
    if user.role != Role.ADMIN and course.teacher_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only the course's teacher or an admin can see this")
    stmt = (select(User).join(Enrollment, Enrollment.user_id == User.id)
            .where(Enrollment.course_id == course_id).order_by(User.id))
    return list(await db.scalars(stmt))


@router.post("/{course_id}/enroll", status_code=status.HTTP_201_CREATED)
async def enroll(course_id: int, user: CanEnroll, db: DB) -> dict[str, int]:
    await get_course(db, course_id)
    db.add(Enrollment(user_id=user.id, course_id=course_id))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Already enrolled") from None
    return {"user_id": user.id, "course_id": course_id}
