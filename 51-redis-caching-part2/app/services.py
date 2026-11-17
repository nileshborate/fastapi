# The decorator in action: the function only talks to the database - the cache is one line
from redis.asyncio import Redis

from app import db
from app.cache import cached
from app.config import get_settings
from app.db import Course


@cached("course:{course_id}", ttl=get_settings().course_ttl)
async def get_course(redis: Redis, course_id: int) -> Course | None:
    return await db.fetch_course(course_id)
