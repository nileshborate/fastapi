# An expensive report, cached for 30 seconds - and how long it has left
import json

from fastapi import APIRouter, Response

from app import db
from app.cache import cache_get, cache_set
from app.config import get_settings
from app.deps import RedisDep

router = APIRouter(prefix="/stats", tags=["Stats"])
STATS_KEY = "stats:popular"


@router.get("/popular")
async def popular(redis: RedisDep, response: Response) -> dict[str, int | str]:
    cached = await cache_get(redis, STATS_KEY)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Cache-TTL"] = str(await redis.ttl(STATS_KEY))   # seconds left
        return json.loads(cached)
    stats = await db.popular_stats()
    await cache_set(redis, STATS_KEY, json.dumps(stats), get_settings().stats_ttl)
    response.headers["X-Cache"] = "MISS"
    return stats
