# Run: python -m demos.headers   (after: alembic upgrade head)
# Development vs production: headers, Host, CORS, HTTPS, /docs - and a crash
import asyncio
import logging

from app.config import Settings
from app.database import engine
from app.main import create_app
from demos.common import client


class OneLine(logging.Handler):
    """the server log: show the id and the real error - in one line"""

    def emit(self, record: logging.LogRecord) -> None:
        error = record.exc_info[1] if record.exc_info else None
        print(f"     server log: {record.getMessage()} -> {error!r}")


async def main() -> None:
    logging.getLogger("coursehub").addHandler(OneLine())
    logging.getLogger("coursehub").propagate = False
    dev = create_app(Settings(environment="development"))
    prod = create_app(Settings(environment="production", allowed_hosts=["api.coursehub.in"],
                               cors_origins=["https://coursehub.in"]))

    async def boom() -> None:
        raise RuntimeError("database password is s3cret!")   # something we never want to show
    prod.add_api_route("/boom", boom)

    async with client(dev) as c:
        r = await c.get("/")
        print("dev  GET /            ", r.status_code)
        for name in ("x-content-type-options", "x-frame-options", "referrer-policy",
                     "cache-control", "strict-transport-security"):
            print(f"     {name:<27} {r.headers.get(name, '- (not sent)')}")
        print("dev  GET /docs        ", (await c.get("/docs")).status_code)
    async with client(prod, "https://api.coursehub.in") as c:
        r = await c.get("/")
        hsts = r.headers["strict-transport-security"]
        print("prod GET /            ", r.status_code, "| HSTS:", hsts)
        print("prod GET /docs        ", (await c.get("/docs")).status_code)
        r = await c.get("/boom")
        print("prod GET /boom        ", r.status_code, r.json())
        r = await c.options("/courses", headers={"Origin": "https://evil.example",
                                                  "Access-Control-Request-Method": "POST"})
        print("prod CORS evil.example", r.status_code, r.text)
        r = await c.options("/courses", headers={"Origin": "https://coursehub.in",
                                                  "Access-Control-Request-Method": "POST"})
        print("prod CORS coursehub.in", r.status_code, r.headers["access-control-allow-origin"])
    async with client(prod, "http://api.coursehub.in") as c:
        r = await c.get("/")
        print("prod http://          ", r.status_code, "->", r.headers["location"])
    async with client(prod, "https://evil.example") as c:
        r = await c.get("/")
        print("prod Host: evil.example", r.status_code, r.text)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
