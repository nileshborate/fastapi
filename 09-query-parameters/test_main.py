# Run:  pytest -v
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_default_pagination() -> None:
    assert len(client.get("/courses").json()) == 5


def test_skip_and_limit() -> None:
    ids = [course["id"] for course in client.get("/courses?skip=2&limit=2").json()]
    assert ids == [3, 4]


def test_filter_by_level() -> None:
    courses = client.get("/courses?level=beginner").json()
    assert {course["level"] for course in courses} == {"beginner"}


def test_bool_parsing() -> None:
    for value in ["false", "0", "no", "off"]:
        courses = client.get(f"/courses?published={value}").json()
        assert [course["id"] for course in courses] == [4]


def test_limit_rules() -> None:
    assert client.get("/courses?limit=0").status_code == 422
    assert client.get("/courses?limit=500").status_code == 422


def test_search_required() -> None:
    assert client.get("/search").status_code == 422


def test_search_min_length() -> None:
    assert client.get("/search?q=a").status_code == 422


def test_search() -> None:
    titles = [course["title"] for course in client.get("/search?q=fastapi").json()]
    assert titles == ["FastAPI Basics", "Deploying FastAPI"]


def test_multiple_values() -> None:
    ids = [course["id"] for course in client.get("/courses/by-ids?ids=1&ids=3").json()]
    assert ids == [1, 3]


def test_path_and_query() -> None:
    assert "price" not in client.get("/courses/2").json()
    assert client.get("/courses/2?include_price=true").json()["price"] == 499
