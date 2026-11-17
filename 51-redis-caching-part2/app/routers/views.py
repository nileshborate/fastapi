# More Redis types: a hash (counters), a sorted set (a leaderboard), a list (recently viewed)
from typing import Annotated

from fastapi import APIRouter, Query, status
from pydantic import BaseModel

from app.deps import RedisDep
from app.routers.courses import CourseId

router = APIRouter(tags=["Views"])
User = Annotated[str, Query(pattern=r"^[a-z]{2,20}$")]
POPULAR = "courses:popular"


def stats_key(course_id: int) -> str:
    return f"course:{course_id}:stats"


def recent_key(user: str) -> str:
    return f"recent:{user}"


@router.post("/courses/{course_id}/views", status_code=status.HTTP_204_NO_CONTENT)
async def add_view(course_id: CourseId, user: User, redis: RedisDep) -> None:
    async with redis.pipeline(transaction=True) as pipe:              # 4 commands, 1 round trip
        pipe.hincrby(stats_key(course_id), "views", 1)                # hash: one field +1
        pipe.zincrby(POPULAR, 1, str(course_id))                      # sorted set: score +1
        pipe.lpush(recent_key(user), course_id)                       # list: add at the front
        pipe.ltrim(recent_key(user), 0, 4)                            # keep only the newest 5
        await pipe.execute()


@router.get("/courses/{course_id}/stats")
async def course_stats(course_id: CourseId, redis: RedisDep) -> dict[str, int]:
    fields = await redis.hgetall(stats_key(course_id))                # {"views": "7"}
    return {name: int(value) for name, value in fields.items()}


class Popular(BaseModel):
    course_id: int
    views: int


@router.get("/popular")
async def popular(redis: RedisDep, n: Annotated[int, Query(ge=1, le=10)] = 3) -> list[Popular]:
    top = await redis.zrange(POPULAR, 0, n - 1, desc=True, withscores=True)   # highest first
    return [Popular(course_id=int(member), views=int(score)) for member, score in top]


@router.get("/users/{user}/recent")
async def recent(user: str, redis: RedisDep) -> list[int]:
    return [int(course_id) for course_id in await redis.lrange(recent_key(user), 0, -1)]
