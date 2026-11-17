# Homework 53: one place to get a Redis client for our own data (tests swap it for fakeredis)
import redis

from app.config import get_settings


def get_store() -> redis.Redis:
    return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)
