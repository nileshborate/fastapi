import os

os.environ["BROKER_URL"] = "memory://"                 # no Redis in the tests
os.environ["RESULT_BACKEND"] = "cache+memory://"       # results in this process's memory
os.environ["EMAIL_SECONDS"] = "0"
os.environ["REPORT_STEP_SECONDS"] = "0"

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.celery_app import celery_app  # noqa: E402
from app.main import app  # noqa: E402

celery_app.conf.update(
    task_always_eager=True,                            # .delay() runs the task right here
    task_store_eager_result=True,                      # ... and keeps the result for /tasks
)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
