# The decorator in action: the function only talks to the database - the cache is one line
from pydantic import BaseModel
from redis.asyncio import Redis

from app import db
from app.cache import cached
from app.config import get_settings
from app.db import Course


@cached("course:{course_id}", ttl=get_settings().course_ttl)
async def get_course(redis: Redis, course_id: int) -> Course | None:
    return await db.fetch_course(course_id)


class Popular(BaseModel):
    course_id: int
    views: int


@cached("popular:{n}", ttl=10)                       # homework 51: the leaderboard, 10 seconds
async def get_popular(redis: Redis, n: int) -> list[Popular]:
    top = await redis.zrange("courses:popular", 0, n - 1, desc=True, withscores=True)
    return [Popular(course_id=int(member), views=int(score)) for member, score in top]
