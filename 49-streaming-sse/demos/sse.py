# Run: python -m demos.sse
# Server-Sent Events on the wire: what the browser really receives - and when
import asyncio

from demos.common import log, reset_clock, serve


async def main() -> None:
    async with serve() as client:
        async with client.stream("GET", "/jobs/export-1/progress?delay=0.5") as response:
            log(f"{response.status_code} · content-type: {response.headers['content-type']}")
            log(f"cache-control: {response.headers['cache-control']} · "
                f"x-accel-buffering: {response.headers['x-accel-buffering']}")
            async for line in response.aiter_lines():
                if line:
                    log(f"| {line}")
        print("\n--- the connection dropped after id 3 - the browser sends Last-Event-ID: 3")
        reset_clock()
        headers = {"Last-Event-ID": "3"}
        async with client.stream("GET", "/jobs/export-1/progress?delay=0.5",
                                 headers=headers) as response:
            async for line in response.aiter_lines():
                if line.startswith(("id:", "event: done")):
                    log(f"| {line}")
        print("\n--- POST /chat/stream: an answer word by word")
        reset_clock()
        words = []
        async with client.stream("POST", "/chat/stream",
                                 json={"text": "What is SSE?"}) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: \""):
                    words.append(line[7:-1])
        log(" ".join(words))


if __name__ == "__main__":
    asyncio.run(main())
