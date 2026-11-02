# Homework answer (Video 25) - shown at the start of Video 26
from fastapi.testclient import TestClient

from tests.conftest import ADMIN, TEACHER

ASHA = {"name": "Asha", "email": "asha@example.com"}
RAHUL = {"name": "Rahul", "email": "rahul@example.com"}


def add(client: TestClient, student: dict) -> dict:
    return client.post("/students", json=student, headers=TEACHER).json()


def test_patch_student(client: TestClient) -> None:
    asha = add(client, ASHA)
    body = client.patch(f"/students/{asha['id']}", json={"name": "Asha K"}, headers=TEACHER).json()
    assert (body["name"], body["email"]) == ("Asha K", "asha@example.com")


def test_patch_duplicate_email_is_409(client: TestClient) -> None:
    add(client, ASHA)
    rahul = add(client, RAHUL)
    response = client.patch(f"/students/{rahul['id']}", json={"email": "asha@example.com"}, headers=TEACHER)
    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


def test_patch_null_is_422(client: TestClient) -> None:
    asha = add(client, ASHA)
    assert client.patch(f"/students/{asha['id']}", json={"email": None}, headers=TEACHER).status_code == 422


def test_delete_student_admin_only(client: TestClient) -> None:
    asha = add(client, ASHA)
    url = f"/students/{asha['id']}"
    assert client.delete(url, headers=TEACHER).status_code == 403
    assert client.delete(url, headers=ADMIN).status_code == 204
    assert client.get(url).status_code == 404


def test_search_sort_and_total(client: TestClient) -> None:
    for name in ["Asha", "Rahul", "Ashwin"]:
        add(client, {"name": name, "email": f"{name.lower()}@example.com"})
    response = client.get("/students", params={"q": "ash", "sort_by": "name", "order": "desc"})
    assert [s["name"] for s in response.json()] == ["Ashwin", "Asha"]
    assert response.headers["X-Total-Count"] == "2"
    assert client.get("/students", params={"sort_by": "password"}).status_code == 422
