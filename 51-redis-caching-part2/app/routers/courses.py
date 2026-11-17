# Endpoints that use the decorated service - and the X-Cache header from a ContextVar
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Response
from pydantic import BaseModel, Field

from app import db, services
from app.cache import cache_status
from app.db import Course
from app.deps import RedisDep

router = APIRouter(prefix="/courses", tags=["Courses"])
CourseId = Annotated[int, Path(ge=1, le=1_000_000)]


@router.get("/{course_id}")
async def read_course(course_id: CourseId, redis: RedisDep, response: Response) -> Course:
    course = await services.get_course(redis, course_id)
    response.headers["X-Cache"] = cache_status.get()       # HIT · MISS · WAIT · SKIP
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


class CourseUpdate(BaseModel):
    price: int = Field(ge=0, le=100_000)


@router.patch("/{course_id}")
async def update_price(course_id: CourseId, data: CourseUpdate, redis: RedisDep) -> Course:
    course = await db.fetch_course(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    updated = course.model_copy(update={"price": data.price})
    await db.save_course(updated)                                       # 1. the database
    await services.get_course.invalidate(redis, course_id=course_id)    # 2. delete the key
    return updated
