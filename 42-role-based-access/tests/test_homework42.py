# Homework 42: GET /courses/{id}/students and PATCH /admin/users/{id}/active
from fastapi.testclient import TestClient



def test_students_of_a_course(client: TestClient, users: dict) -> None:
    ravi, meera, asha = users["teacher"], users["student"], users["admin"]
    client.post("/courses", json={"title": "FastAPI Basics", "fee": 299}, headers=ravi)
    client.post("/courses/1/enroll", headers=meera)
    response = client.get("/courses/1/students", headers=ravi)          # his course
    assert response.status_code == 200
    assert [s["email"] for s in response.json()] == ["meera@example.com"]
    assert client.get("/courses/1/students", headers=asha).status_code == 200     # admin
    assert client.get("/courses/1/students", headers=meera).status_code == 403    # student
    assert client.get("/courses/1/students").status_code == 401
    assert client.get("/courses/9/students", headers=asha).status_code == 404


def test_another_teacher_cant_see_them(client: TestClient, users: dict) -> None:
    asha, ravi = users["admin"], users["teacher"]
    client.post("/courses", json={"title": "Docker Basics", "fee": 399}, headers=asha)
    assert client.get("/courses/1/students", headers=ravi).status_code == 403   # not his


def test_block_a_user(client: TestClient, users: dict) -> None:
    asha, meera = users["admin"], users["student"]
    response = client.patch("/admin/users/3/active", json={"is_active": False}, headers=asha)
    assert response.status_code == 200 and response.json()["is_active"] is False
    assert client.get("/me", headers=meera).status_code == 403            # old token
    form = {"username": "meera@example.com", "password": "blue-river-42"}
    assert client.post("/token", data=form).status_code == 401           # no new login
    response = client.patch("/admin/users/1/active", json={"is_active": False}, headers=asha)
    assert response.status_code == 400                                   # not yourself
    response = client.patch("/admin/users/3/active", json={"is_active": False},
                            headers=users["teacher"])
    assert response.status_code == 403                                   # admins only
