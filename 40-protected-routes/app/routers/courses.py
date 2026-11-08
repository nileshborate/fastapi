# Public reading, protected writing, and only the OWNER may change a course
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import DB, CurrentUser, OptionalUser
from app.models import Course
from app.schemas import CourseIn, CourseOut, CourseUpdate

router = APIRouter(prefix="/courses", tags=["Courses"])


def to_out(course: Course, user_id: int | None) -> CourseOut:
    out = CourseOut.model_validate(course)
    out.is_mine = course.owner_id == user_id
    return out


@router.get("", response_model=list[CourseOut])
async def list_courses(db: DB, user: OptionalUser) -> list[CourseOut]:
    # PUBLIC: works without a token - with a token, we can say "is_mine"
    courses = await db.scalars(select(Course).order_by(Course.id))
    return [to_out(c, user.id if user else None) for c in courses]


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(data: CourseIn, user: CurrentUser, db: DB) -> CourseOut:
    # PROTECTED: no token -> 401 before this line runs
    course = Course(**data.model_dump(), owner_id=user.id)   # the owner: from the TOKEN
    db.add(course)
    await db.commit()
    return to_out(course, user.id)


async def get_own_course(course_id: int, user_id: int, db: DB) -> Course:
    course = await db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if course.owner_id != user_id:                  # logged in - but not YOUR course
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only the owner can change this course")
    return course


@router.patch("/{course_id}", response_model=CourseOut)
async def update_course(course_id: int, data: CourseUpdate, user: CurrentUser,
                        db: DB) -> CourseOut:
    course = await get_own_course(course_id, user.id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    await db.commit()
    return to_out(course, user.id)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id: int, user: CurrentUser, db: DB) -> None:
    course = await get_own_course(course_id, user.id, db)
    await db.delete(course)
    await db.commit()
