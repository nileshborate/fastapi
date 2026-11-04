# Run: python -m demos.gather       (after: alembic upgrade head)
import asyncio
import time

from sqlalchemy import func, select
from sqlalchemy.exc import InvalidRequestError

from app.database import SessionLocal, engine
from app.models import Course, Teacher


async def slow_call(name: str) -> str:
    await asyncio.sleep(0.5)                    # pretend: a query that takes 0.5 s
    return name


async def part1_one_by_one_vs_gather() -> None:
    start = time.perf_counter()
    a = await slow_call("A")
    b = await slow_call("B")
    c = await slow_call("C")
    print(f"1. one by one: {[a, b, c]} in {time.perf_counter() - start:.2f} s")

    start = time.perf_counter()
    results = await asyncio.gather(slow_call("A"), slow_call("B"), slow_call("C"))
    print(f"2. gather:     {results} in {time.perf_counter() - start:.2f} s")


async def part2_one_session_is_not_enough() -> None:
    count_teachers = select(func.count()).select_from(Teacher)
    count_courses = select(func.count()).select_from(Course)
    async with SessionLocal() as db:            # ONE session for two tasks - WRONG
        results = await asyncio.gather(db.scalar(count_teachers), db.scalar(count_courses),
                                       return_exceptions=True)
        error = next(r for r in results if isinstance(r, InvalidRequestError))
        print("3. one session:", type(error).__name__, "-", str(error).split(" (")[0])

    async def count(stmt) -> int:               # noqa: ANN001
        async with SessionLocal() as db:        # FIX: every task gets its own session
            return await db.scalar(stmt)

    print("4. own sessions:", await asyncio.gather(count(count_teachers), count(count_courses)))
    await engine.dispose()


async def main() -> None:
    await part1_one_by_one_vs_gather()
    await part2_one_session_is_not_enough()


if __name__ == "__main__":
    asyncio.run(main())
