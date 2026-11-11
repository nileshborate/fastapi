# Run: python -m demos.threads
# WHO runs my endpoint? And what happens with more blocking requests than threads?
import asyncio

from demos.common import HTTP, serve, together


async def main() -> None:
    async with serve() as client:
        for path in ("/ping", "/io/async-await?seconds=0", "/io/sync?seconds=0",
                     "/io/offload?seconds=0"):
            data = (await client.get(f"{HTTP}{path}")).json()
            print(f"{path:<28} runs in: {data['thread']}")
        info = (await client.get(f"{HTTP}/threadpool")).json()
        print(f"\nthe threadpool has {info['threads']} threads")
        for n in (40, 41, 80):
            seconds = await together(client, "/io/sync?seconds=0.5", n)
            print(f"{n:>3} x def + time.sleep(0.5)  -> all answered after {seconds:5.2f} s")


if __name__ == "__main__":
    asyncio.run(main())
