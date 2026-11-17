# Part 1's cache-aside, without a lock - only to compare in the stampede demo
from fastapi import APIRouter, HTTPException

from app import db
from app.db import Course
from app.deps import RedisDep
from app.routers.courses import CourseId

router = APIRouter(prefix="/naive", tags=["Demo"])


@router.get("/courses/{course_id}")
async def read_course_naive(course_id: CourseId, redis: RedisDep) -> Course:
    key = f"naive:course:{course_id}"
    cached = await redis.get(key)
    if cached is not None:
        return Course.model_validate_json(cached)
    course = await db.fetch_course(course_id)                 # every waiting request gets here
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    await redis.set(key, course.model_dump_json(), ex=60)
    return course
