# More Redis types: a hash (counters), a sorted set (a leaderboard), a list (recently viewed)
from typing import Annotated

from fastapi import APIRouter, Query, status
from pydantic import BaseModel

from app import services
from app.deps import RedisDep
from app.routers.courses import CourseId
from app.services import Popular

router = APIRouter(tags=["Views"])
User = Annotated[str, Query(pattern=r"^[a-z]{2,20}$")]
POPULAR = "courses:popular"


def stats_key(course_id: int) -> str:
    return f"course:{course_id}:stats"


def recent_key(user: str) -> str:
    return f"recent:{user}"


def likers_key(course_id: int) -> str:
    return f"course:{course_id}:likers"                               # homework 51: a SET


@router.post("/courses/{course_id}/views", status_code=status.HTTP_204_NO_CONTENT)
async def add_view(course_id: CourseId, user: User, redis: RedisDep) -> None:
    async with redis.pipeline(transaction=True) as pipe:              # 4 commands, 1 round trip
        pipe.hincrby(stats_key(course_id), "views", 1)                # hash: one field +1
        pipe.zincrby(POPULAR, 1, str(course_id))                      # sorted set: score +1
        pipe.lpush(recent_key(user), course_id)                       # list: add at the front
        pipe.ltrim(recent_key(user), 0, 4)                            # keep only the newest 5
        await pipe.execute()


class Like(BaseModel):
    new: bool                                                         # False: liked before
    likes: int


@router.post("/courses/{course_id}/likes")
async def add_like(course_id: CourseId, user: User, redis: RedisDep) -> Like:
    added = await redis.sadd(likers_key(course_id), user)     # 1 = new · 0 = already in
    return Like(new=added == 1, likes=await redis.scard(likers_key(course_id)))


@router.get("/courses/{course_id}/stats")
async def course_stats(course_id: CourseId, redis: RedisDep) -> dict[str, int]:
    async with redis.pipeline(transaction=False) as pipe:
        pipe.hget(stats_key(course_id), "views")                      # the hash
        pipe.scard(likers_key(course_id))                             # the set: its size
        views, likes = await pipe.execute()
    return {"views": int(views or 0), "likes": likes}


@router.get("/popular")
async def popular(redis: RedisDep, n: Annotated[int, Query(ge=1, le=10)] = 3) -> list[Popular]:
    return await services.get_popular(redis, n)                       # homework: @cached


@router.get("/users/{user}/recent")
async def recent(user: str, redis: RedisDep) -> list[int]:
    return [int(course_id) for course_id in await redis.lrange(recent_key(user), 0, -1)]
