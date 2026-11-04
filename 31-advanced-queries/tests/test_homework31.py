# Homework answer (Video 31): students page, top students, sort
from fastapi.testclient import TestClient


def test_students_with_course_counts(client: TestClient) -> None:
    body = client.get("/students", params={"city": "Pune", "size": 2}).json()
    assert body["items"] == [
        {"id": 1, "name": "Asha", "city": "Pune", "courses": 3},
        {"id": 3, "name": "Meera", "city": "Pune", "courses": 2},
    ]
    assert (body["total"], body["pages"]) == (3, 2)          # Asha, Meera, Dev


def test_students_last_page_has_a_zero(client: TestClient) -> None:
    body = client.get("/students", params={"city": "Pune", "size": 2, "page": 2}).json()
    assert body["items"] == [{"id": 6, "name": "Dev", "city": "Pune", "courses": 0}]


def test_top_students(client: TestClient) -> None:
    assert client.get("/reports/top-students", params={"limit": 3}).json() == [
        {"name": "Sara", "average_grade": 95.0},
        {"name": "Meera", "average_grade": 88.0},             # her ungraded course is ignored
        {"name": "Asha", "average_grade": 85.0},
    ]


def test_sort_courses(client: TestClient) -> None:
    def titles(sort: str) -> list[str]:
        body = client.get("/courses", params={"sort": sort, "size": 3}).json()
        return [c["title"] for c in body["items"]]

    assert titles("-fee") == ["System Design", "Docker Deep Dive", "React Basics"]
    assert titles("fee") == ["Python 101", "SQL for Beginners", "FastAPI Basics"]
    assert titles("title") == ["Docker Deep Dive", "FastAPI Basics", "Python 101"]
    assert client.get("/courses", params={"sort": "drop table"}).status_code == 422
