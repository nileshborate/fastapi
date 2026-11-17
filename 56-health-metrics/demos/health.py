# Liveness vs readiness - with a healthy, a slow, a broken and a draining server
import asyncio

from app import health
from app.config import get_settings
from app.main import app
from demos.common import payments, serve


async def show(client, label: str, url: str = "/health/ready") -> None:
    r = await client.get(url)
    body = r.json()
    checks = body.pop("checks", {})
    print(f"{label:<22} {r.status_code} {body}")
    for name, c in checks.items():
        print(f"{'':<26}{name:<10} {c}")


async def main() -> None:
    async with serve() as client:
        await show(client, "live", "/health/live")
        await show(client, "all good")
        payments.state.delay = 3                    # payments hangs ...
        await show(client, "payments slow")
        payments.state.delay, payments.state.up = 0, False
        await show(client, "payments 503")
        payments.state.up = True
        get_settings().db_path = "/no/such/folder/coursehub.db"    # the database is gone
        await show(client, "database broken")
        await show(client, "live (still!)", "/health/live")
        get_settings().db_path = "demo.db"
        app.state.shutting_down = True              # what the lifespan does on shutdown
        await show(client, "shutting down")
        app.state.shutting_down = False
    print("timeout per check:", get_settings().check_timeout, "s ·", list(health.CHECKS))


asyncio.run(main())
