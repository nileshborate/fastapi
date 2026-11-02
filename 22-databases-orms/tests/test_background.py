from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.tasks import send_welcome_email, write_log
from tests.conftest import ADMIN, TEACHER


def use_log_file(log: Path) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(log_file=log, email_delay_seconds=0)


def test_welcome_email_is_sent_in_the_background(client: TestClient, tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    use_log_file(log)
    response = client.post("/students", json={"name": "Asha", "email": "asha@example.com"}, headers=TEACHER)
    assert response.status_code == 201
    # the TestClient waits for background tasks, so the email is already "sent" here
    assert "welcome email sent to Asha <asha@example.com>" in log.read_text()


def test_no_email_when_the_request_fails(client: TestClient, tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    use_log_file(log)
    response = client.post("/students", json={"name": "A", "email": "not-an-email"}, headers=TEACHER)
    assert response.status_code == 422
    assert not log.exists()                     # the endpoint never ran -> no task was added


def test_audit_log_from_a_dependency(client: TestClient, tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    use_log_file(log)
    client.get("/admin/stats", headers=ADMIN)
    assert "audit: GET /admin/stats" in log.read_text()


def test_task_functions_are_plain_python(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    write_log("hello", log)
    send_welcome_email("Ravi", "ravi@example.com", log, delay=0)
    lines = log.read_text().splitlines()
    assert lines[0].endswith("hello")
    assert lines[1].endswith("welcome email sent to Ravi <ravi@example.com>")


def test_course_created_is_logged(client: TestClient, tmp_path: Path) -> None:      # homework (Video 21)
    log = tmp_path / "app.log"
    use_log_file(log)
    client.post("/courses", json={"title": "Docker Basics", "price": 99}, headers=TEACHER)
    assert "course created: Docker Basics" in log.read_text()
