from fastapi.testclient import TestClient

from tests.conftest import TEACHER


def test_teachers_with_pagination(client: TestClient) -> None:           # homework answer (Video 17)
    for name in ["Nilesh", "Priya", "Rahul"]:
        client.post("/teachers", json={"name": name, "subject": "FastAPI"}, headers=TEACHER)
    assert [t["name"] for t in client.get("/teachers", params={"skip": 1, "limit": 1}, headers=TEACHER).json()] == ["Priya"]


def test_teacher_404(client: TestClient) -> None:
    assert client.get("/teachers/7", headers=TEACHER).json() == {"detail": "Teacher not found"}


def test_teachers_router_needs_staff_role(client: TestClient) -> None:    # homework answer (Video 18)
    assert client.get("/teachers").status_code == 403                    # default role: student
