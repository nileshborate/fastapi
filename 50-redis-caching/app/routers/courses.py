# The cache-aside pattern: look in Redis first - on a miss, ask the database and remember it
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Response
from pydantic import BaseModel, Field, TypeAdapter

from app import db
from app.cache import ALL_COURSES_KEY, cache_delete, cache_get, cache_set, course_key
from app.config import get_settings
from app.db import Course
from app.deps import RedisDep

router = APIRouter(prefix="/courses", tags=["Courses"])
CourseId = Annotated[int, Path(ge=1, le=1_000_000)]
CourseList = TypeAdapter(list[Course])               # homework 50: JSON <-> list[Course]


@router.get("")
async def list_courses(redis: RedisDep, response: Response) -> list[Course]:
    cached = await cache_get(redis, ALL_COURSES_KEY)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        return CourseList.validate_json(cached)
    courses = await db.fetch_all_courses()
    await cache_set(redis, ALL_COURSES_KEY, CourseList.dump_json(courses).decode(),
                    get_settings().course_ttl)
    response.headers["X-Cache"] = "MISS"
    return courses


@router.get("/{course_id}")
async def read_course(course_id: CourseId, redis: RedisDep, response: Response) -> Course:
    key = course_key(course_id)
    cached = await cache_get(redis, key)                       # 1. ask the cache
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        return Course.model_validate_json(cached)              # 2. HIT: no database at all

    course = await db.fetch_course(course_id)                  # 3. MISS: ask the database
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    await cache_set(redis, key, course.model_dump_json(), get_settings().course_ttl)  # 4.
    response.headers["X-Cache"] = "MISS"
    return course


class CourseUpdate(BaseModel):
    price: int = Field(ge=0, le=100_000)


@router.patch("/{course_id}")
async def update_price(course_id: CourseId, data: CourseUpdate, redis: RedisDep) -> Course:
    course = await db.fetch_course(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    updated = course.model_copy(update={"price": data.price})
    await db.save_course(updated)                              # 1. write the database
    await cache_delete(redis, course_key(course_id), ALL_COURSES_KEY)  # 2. THEN delete both
    return updated
