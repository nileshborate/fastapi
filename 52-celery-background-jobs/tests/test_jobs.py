# The API sends tasks - and the tasks run here (eager), so we can check the results
import pytest
from fastapi.testclient import TestClient

from app.tasks import build_report, send_welcome_email


def test_register_sends_a_task(client: TestClient) -> None:
    user = {"email": "asha@example.com", "name": "Asha"}
    response = client.post("/users/register", json=user)
    assert response.status_code == 201
    status = client.get(f"/tasks/{response.json()['task_id']}").json()
    assert status["state"] == "SUCCESS"
    assert status["result"]["to"] == "asha@example.com"


def test_register_only_queues(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    class FakeResult:
        id = "11111111-1111-1111-1111-111111111111"

    def fake_delay(*args: str) -> FakeResult:
        calls.append(args)
        return FakeResult()

    monkeypatch.setattr(send_welcome_email, "delay", fake_delay)     # don't run it at all
    user = {"email": "ravi@example.com", "name": "Ravi"}
    response = client.post("/users/register", json=user)
    assert response.json()["task_id"] == FakeResult.id
    assert calls == [("ravi@example.com", "Ravi")]                   # simple JSON arguments


def test_report_progress_and_result(client: TestClient) -> None:
    response = client.post("/reports/3")
    assert response.status_code == 202
    status = client.get(response.headers["location"]).json()
    assert status["state"] == "SUCCESS"
    assert status["result"] == {"course_id": 3, "title": "FastAPI Mastery",
                                "students": 2500, "rows": 10000}


def test_report_failure(client: TestClient) -> None:
    response = client.post("/reports/99")
    status = client.get(response.headers["location"]).json()
    assert status["state"] == "FAILURE"
    assert "course 99 not found" in status["error"]


def test_task_status_edge_cases(client: TestClient) -> None:
    unknown = client.get("/tasks/00000000-0000-0000-0000-000000000000").json()
    assert unknown["state"] == "PENDING"           # Celery can't tell "unknown" from "waiting"
    assert client.get("/tasks/not-a-uuid").status_code == 422
    bad = {"email": "not-an-email", "name": "A"}
    assert client.post("/users/register", json=bad).status_code == 422


def test_a_task_is_still_a_function() -> None:
    assert send_welcome_email("meera@example.com", "Meera")["to"] == "meera@example.com"
    assert build_report.apply(args=(1,)).get()["rows"] == 4800      # bind=True: needs a task id
