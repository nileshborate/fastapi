# Run: python -m demos.stacking
# How SecurityScopes collects scopes along the dependency chain - in a tiny app
import asyncio
from typing import Annotated

import httpx
from fastapi import FastAPI, Security
from fastapi.security import SecurityScopes

app = FastAPI()
calls: list[list[str]] = []


async def check(security_scopes: SecurityScopes) -> list[str]:
    calls.append(security_scopes.scopes)              # what did THIS call need?
    return security_scopes.scopes


async def teacher(scopes: Annotated[list[str], Security(check, scopes=["courses:read"])]):
    return scopes


@app.get("/stacked")
async def stacked(scopes: Annotated[list[str], Security(teacher, scopes=["courses:write"])]):
    return scopes


@app.get("/twice", dependencies=[Security(check, scopes=["me"])])
async def twice(a: Annotated[list[str], Security(check, scopes=["me"])],
                b: Annotated[list[str], Security(check, scopes=["courses:read"])]):
    return [a, b]


async def main() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                 base_url="http://test") as c:
        print("1. GET /stacked ->", (await c.get("/stacked")).json())
        calls.clear()
        print("2. GET /twice   ->", (await c.get("/twice")).json())
        print("   check() ran", len(calls), "times:", calls)


if __name__ == "__main__":
    asyncio.run(main())
