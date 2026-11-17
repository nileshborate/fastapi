# Homework 50: clear one course from the cache by hand (e.g. after a manual fix in the database)
from fastapi import APIRouter, Response, status

from app.cache import cache_delete, course_key
from app.deps import RedisDep
from app.routers.courses import CourseId

router = APIRouter(prefix="/cache", tags=["Cache"])


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_course(course_id: CourseId, redis: RedisDep) -> Response:
    await cache_delete(redis, course_key(course_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
