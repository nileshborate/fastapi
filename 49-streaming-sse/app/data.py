# Fake data for the streams - so we can focus on HOW the data travels
import asyncio
from collections.abc import AsyncIterator, Iterator

from pydantic import BaseModel

TITLES = ["Python Basics", "SQL Joins", "FastAPI CRUD", "Docker 101", "Async Python"]


class Lesson(BaseModel):
    id: int
    title: str
    minutes: int


def csv_rows(count: int) -> Iterator[str]:
    """one CSV line at a time - never the whole file in memory"""
    yield "id,title,minutes\n"
    for n in range(1, count + 1):
        yield f"{n},{TITLES[n % len(TITLES)]} {n},{10 + n % 50}\n"


def csv_chunks(count: int, lines_per_chunk: int = 1000) -> Iterator[str]:
    """the same lines - but sent in batches: one tiny chunk per line is VERY slow"""
    batch: list[str] = []
    for line in csv_rows(count):
        batch.append(line)
        if len(batch) == lines_per_chunk:
            yield "".join(batch)
            batch.clear()
    if batch:
        yield "".join(batch)


async def slow_lessons(count: int, delay: float) -> AsyncIterator[Lesson]:
    """lessons that arrive one by one - like rows from a slow query"""
    for n in range(1, count + 1):
        await asyncio.sleep(delay)
        yield Lesson(id=n, title=f"{TITLES[n % len(TITLES)]} {n}", minutes=10 + n % 50)
