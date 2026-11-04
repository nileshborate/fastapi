# Run: python -m demos.pool   - a TINY pool: 2 connections + 1 extra, wait max 1 second
import asyncio
import time

from sqlalchemy import text
from sqlalchemy.exc import TimeoutError as PoolTimeout
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings

engine = create_async_engine(get_settings().database_url,
                             pool_size=2, max_overflow=1, pool_timeout=1)
START = time.perf_counter()


async def job(n: int) -> None:
    try:
        async with engine.connect() as conn:        # take a connection from the pool
            await conn.execute(text("SELECT 1"))
            print(f"{time.perf_counter() - START:4.1f} s  job {n}: got a connection")
            await asyncio.sleep(1.5)                # ...and keep it for 1.5 s
    except PoolTimeout as error:
        print(f"{time.perf_counter() - START:4.1f} s  job {n}: {str(error).split(',')[0]}")


async def main() -> None:
    await asyncio.gather(*(job(n) for n in range(1, 6)))     # 5 jobs, 3 connections
    print("checked out now:", engine.pool.checkedout())
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
