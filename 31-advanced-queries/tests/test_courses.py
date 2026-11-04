# GET /courses: filters across tables + pagination with totals
from fastapi.testclient import TestClient


def titles(body: dict) -> list[str]:
    return [c["title"] for c in body["items"]]


def test_all_courses_with_the_teacher_name(client: TestClient) -> None:
    body = client.get("/courses").json()
    assert body["total"] == 6
    assert body["items"][0] == {"id": 1, "title": "FastAPI Basics", "level": "beginner",
                                "fee": 299.0, "teacher": "Nilesh"}


def test_filter_by_a_column_of_another_table(client: TestClient) -> None:
    body = client.get("/courses", params={"teacher": "nil"}).json()
    assert titles(body) == ["FastAPI Basics", "Docker Deep Dive", "System Design"]
    assert body["total"] == 3


def test_filters_combine(client: TestClient) -> None:
    body = client.get("/courses", params={"level": "beginner", "max_fee": 250}).json()
    assert titles(body) == ["Python 101", "SQL for Beginners"]


def test_search_escapes_wildcards(client: TestClient) -> None:
    assert client.get("/courses", params={"q": "%"}).json()["total"] == 0


def test_pagination_with_totals(client: TestClient) -> None:
    body = client.get("/courses", params={"size": 2, "page": 2}).json()
    assert titles(body) == ["System Design", "Python 101"]
    assert (body["total"], body["page"], body["size"], body["pages"]) == (6, 2, 2, 3)
    last = client.get("/courses", params={"size": 4, "page": 2}).json()
    assert titles(last) == ["SQL for Beginners", "React Basics"]       # the last page: only 2


def test_page_after_the_end_is_empty(client: TestClient) -> None:
    body = client.get("/courses", params={"page": 9}).json()
    assert body["items"] == [] and body["total"] == 6


def test_bad_query_parameters(client: TestClient) -> None:
    assert client.get("/courses", params={"size": 0}).status_code == 422
    assert client.get("/courses", params={"level": "expert"}).status_code == 422
    # extra="forbid": an unknown parameter is a 422, not silently ignored
    assert client.get("/courses", params={"colour": "red"}).status_code == 422
