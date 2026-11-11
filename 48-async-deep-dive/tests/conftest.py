from collections.abc import AsyncIterator

import httpx
import pytest

from app.main import app, lifespan


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    async with lifespan(app):                     # ASGITransport skips the lifespan: start it
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
