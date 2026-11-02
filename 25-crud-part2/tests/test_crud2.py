# Video 25 - CRUD Part 2: Update, Delete, search, sorting (+ the homework answer from Video 24)
from fastapi.testclient import TestClient

from tests.conftest import ADMIN, TEACHER

DOCKER = {"title": "Docker Basics", "price": 99}


def add(client: TestClient, title: str, price: float) -> dict:
    return client.post("/courses", json={"title": title, "price": price}, headers=TEACHER).json()


# ---------------------------------------------------------------- homework answer (Video 24)
def test_course_by_title(client: TestClient) -> None:
    add(client, "Docker Basics", 99)
    assert client.get("/courses/by-title/Docker Basics").json()["price"] == 99
    assert client.get("/courses/by-title/Nothing").json() == {"detail": "Course not found"}


def test_duplicate_teacher_email_is_409(client: TestClient) -> None:
    meera = {"name": "Meera", "email": "meera@example.com", "subject": "Python"}
    assert client.post("/teachers", json=meera, headers=TEACHER).status_code == 201
    response = client.post("/teachers", json={**meera, "name": "Meera K"}, headers=TEACHER)
    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


def test_teacher_dep(client: TestClient) -> None:
    response = client.get("/teachers/42", headers=TEACHER)
    assert response.status_code == 404
    assert response.json() == {"detail": "Teacher not found"}


# ---------------------------------------------------------------- PUT = replace the whole course
def test_put_replaces_the_course(client: TestClient) -> None:
    course = add(client, "Docker Basics", 99)
    assert course["updated_at"] is None                                # never updated yet
    body = {"title": "Docker Complete", "price": 149}
    updated = client.put(f"/courses/{course['id']}", json=body, headers=TEACHER).json()
    assert updated["title"] == "Docker Complete" and updated["price"] == 149
    assert updated["id"] == course["id"] and updated["created_at"] == course["created_at"]
    assert updated["updated_at"] is not None                           # filled by onupdate


def test_put_needs_every_field(client: TestClient) -> None:
    course = add(client, "Docker Basics", 99)
    response = client.put(f"/courses/{course['id']}", json={"price": 149}, headers=TEACHER)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]


# ---------------------------------------------------------------- PATCH = change only some fields
def test_patch_changes_only_the_sent_fields(client: TestClient) -> None:
    course = add(client, "Docker Basics", 99)
    updated = client.patch(f"/courses/{course['id']}", json={"price": 79}, headers=TEACHER).json()
    assert updated["price"] == 79
    assert updated["title"] == "Docker Basics"                         # untouched


def test_patch_rejects_null_and_unknown_fields(client: TestClient) -> None:
    course = add(client, "Docker Basics", 99)
    url = f"/courses/{course['id']}"
    assert client.patch(url, json={"title": None}, headers=TEACHER).status_code == 422
    response = client.patch(url, json={"id": 7}, headers=TEACHER)
    assert response.json()["detail"][0]["type"] == "extra_forbidden"
    assert client.patch(url, json={"price": -5}, headers=TEACHER).status_code == 422


def test_update_to_an_existing_title_is_409(client: TestClient) -> None:
    add(client, "Docker Basics", 99)
    second = add(client, "Kubernetes", 199)
    url = f"/courses/{second['id']}"
    response = client.patch(url, json={"title": "Docker Basics"}, headers=TEACHER)
    assert response.status_code == 409
    assert response.json() == {"detail": "Course title already exists"}
    assert client.get(url).json()["title"] == "Kubernetes"             # rollback: nothing changed


def test_update_missing_course_is_404(client: TestClient) -> None:
    assert client.put("/courses/99", json=DOCKER, headers=TEACHER).status_code == 404
    assert client.patch("/courses/99", json={"price": 1}, headers=TEACHER).status_code == 404


def test_update_needs_staff(client: TestClient) -> None:
    course = add(client, "Docker Basics", 99)
    student = {"X-API-Key": "test-key", "X-Role": "student"}
    assert client.patch(f"/courses/{course['id']}", json={"price": 1}, headers=student).status_code == 403


# ---------------------------------------------------------------- DELETE
def test_delete_then_404(client: TestClient) -> None:
    course = add(client, "Docker Basics", 99)
    url = f"/courses/{course['id']}"
    response = client.delete(url, headers=ADMIN)
    assert response.status_code == 204 and response.content == b""    # 204 = success, NO body
    assert client.get(url).status_code == 404
    assert client.delete(url, headers=ADMIN).status_code == 404        # already gone


# ---------------------------------------------------------------- search + sorting + total
def test_search_ignores_case(client: TestClient) -> None:
    for title, price in [("Docker Basics", 99), ("Advanced docker", 199), ("Python", 49)]:
        add(client, title, price)
    titles = [c["title"] for c in client.get("/courses", params={"q": "DOCKER"}).json()]
    assert titles == ["Docker Basics", "Advanced docker"]


def test_search_percent_is_just_a_character(client: TestClient) -> None:
    add(client, "Python 100% Practical", 99)
    add(client, "Docker", 99)
    titles = [c["title"] for c in client.get("/courses", params={"q": "%"}).json()]
    assert titles == ["Python 100% Practical"]                         # autoescape=True


def test_sort_by_price_desc(client: TestClient) -> None:
    for title, price in [("Docker", 99), ("Python", 49), ("Kubernetes", 199)]:
        add(client, title, price)
    response = client.get("/courses", params={"sort_by": "price", "order": "desc"})
    assert [c["price"] for c in response.json()] == [199, 99, 49]


def test_sort_by_unknown_column_is_422(client: TestClient) -> None:
    response = client.get("/courses", params={"sort_by": "password"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "literal_error"


def test_total_count_header(client: TestClient) -> None:
    for i in range(5):
        add(client, f"Docker part {i}", 10 * i)
    add(client, "Python", 49)
    response = client.get("/courses", params={"q": "docker", "limit": 2})
    assert len(response.json()) == 2                                   # one page ...
    assert response.headers["X-Total-Count"] == "5"                    # ... of 5 matches


def test_cors_allows_patch(client: TestClient) -> None:
    headers = {"Origin": "http://localhost:3000", "Access-Control-Request-Method": "PATCH"}
    response = client.options("/courses/1", headers=headers)
    assert response.status_code == 200
    assert "PATCH" in response.headers["access-control-allow-methods"]
