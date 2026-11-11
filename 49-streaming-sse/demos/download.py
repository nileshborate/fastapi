# Run: python -m demos.download
# 1,000,000 CSV rows: when does the FIRST byte arrive - and how much memory does it take?
import asyncio
import time
import tracemalloc

import httpx

from demos.common import serve


async def timing(client: httpx.AsyncClient, path: str) -> tuple[float, float, int]:
    start = time.perf_counter()
    first, size = None, 0
    async with client.stream("GET", path) as response:
        async for chunk in response.aiter_bytes():
            first = first or time.perf_counter() - start        # time to first byte
            size += len(chunk)
    return first or 0.0, time.perf_counter() - start, size


async def peak_memory(client: httpx.AsyncClient, path: str) -> float:
    tracemalloc.start()                                       # the server runs in THIS process
    await timing(client, path)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return peak / 1_000_000


async def main() -> None:
    async with serve() as client:
        for label, path in (("PlainTextResponse (all at once)", "/export/buffered"),
                            ("StreamingResponse (1,000 lines)", "/export/streamed")):
            url = f"{path}?rows=1000000"
            first, total, size = await timing(client, url)
            peak = await peak_memory(client, url)
            print(f"{label:<32} first byte {first:4.2f} s · last {total:4.2f} s · "
                  f"{size / 1e6:.1f} MB · peak memory {peak:5.1f} MB")
        first, total, size = await timing(client, "/export/line-by-line?rows=20000")
        print(f"{'line by line - 20,000 rows only':<32} first byte {first:4.2f} s · "
              f"last {total:4.2f} s · {size / 1e6:.1f} MB")
        r = await client.get("/files/report")
        size = r.headers["content-length"]
        print(f"\nFileResponse /files/report  {r.status_code}  {size} bytes")
        for name in ("accept-ranges", "content-disposition", "etag"):
            print(f"   {name:<20} {r.headers[name]}")
        r = await client.get("/files/report", headers={"Range": "bytes=0-49"})
        print(f"Range: bytes=0-49  ->  {r.status_code} Partial Content · "
              f"content-range: {r.headers['content-range']}")
        print(f"   {r.text!r}")


if __name__ == "__main__":
    asyncio.run(main())
