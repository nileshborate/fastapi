from fastapi.testclient import TestClient


def test_teachers_with_pagination(client: TestClient) -> None:           # homework answer (Video 17)
    for name in ["Nilesh", "Priya", "Rahul"]:
        client.post("/teachers", json={"name": name, "subject": "FastAPI"})
    assert [t["name"] for t in client.get("/teachers", params={"skip": 1, "limit": 1}).json()] == ["Priya"]


def test_teacher_404(client: TestClient) -> None:
    assert client.get("/teachers/7").json() == {"detail": "Teacher not found"}
