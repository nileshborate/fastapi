from fastapi.testclient import TestClient

from app import dependencies
from app.dependencies import get_role
from app.main import app
from tests.conftest import ADMIN, TEACHER


def test_router_level_dependencies(client: TestClient) -> None:
    assert client.get("/admin/stats", headers={"X-Role": "admin"}).status_code == 422          # no API key
    assert client.get("/admin/stats", headers={"X-API-Key": "nope"}).status_code == 401
    assert client.get("/admin/stats", headers=TEACHER).status_code == 403
    assert client.get("/admin/stats", headers=ADMIN).json() == {"courses": 0, "students": 0, "checked_by": "admin"}


def test_yield_dependency_cleans_up(client: TestClient) -> None:
    client.get("/admin/stats", headers=ADMIN)
    assert dependencies.EVENTS == ["session opened", "session closed"]


def test_sub_dependency_is_cached(client: TestClient) -> None:
    calls: list[int] = []

    def counting_role() -> str:
        calls.append(1)
        return "admin"

    app.dependency_overrides[get_role] = counting_role
    client.get("/admin/stats", headers={"X-API-Key": ADMIN["X-API-Key"]})
    assert len(calls) == 1        # used by require_admin AND the endpoint - called once
