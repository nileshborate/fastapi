# The rate limiter alone (with a fake clock), and on the login
from fastapi.testclient import TestClient

from app.ratelimit import RateLimiter
from tests.conftest import PASSWORD, auth


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_sliding_window() -> None:
    clock = FakeClock()
    limiter = RateLimiter(3, 60, clock=clock)
    for _ in range(3):
        limiter.check("asha")
    try:
        limiter.check("asha")
        raise AssertionError("the 4th request must fail")
    except Exception as error:                                 # HTTPException
        assert error.status_code == 429 and error.headers["Retry-After"] == "60"
    limiter.check("ravi")                                      # another key: its own window
    clock.now += 60                                            # one minute later ...
    limiter.check("asha")                                      # ... the old hits are gone


def test_login_brute_force(client: TestClient) -> None:
    auth(client)                                               # 1 login
    wrong = {"username": "asha@example.com", "password": "wrong-password"}
    codes = [client.post("/token", data=wrong).status_code for _ in range(5)]
    assert codes == [401, 401, 401, 401, 429]
    right = {"username": "asha@example.com", "password": PASSWORD}
    response = client.post("/token", data=right)
    assert response.status_code == 429                         # even the right password
    assert int(response.headers["retry-after"]) > 0
    other = {"username": "ravi@example.com", "password": "x" * 8}
    assert client.post("/token", data=other).status_code == 401   # its own counter


def test_writes_per_user(client: TestClient) -> None:
    headers = auth(client)
    codes = [client.post("/courses", json={"title": f"Course {n}", "fee": 1},
                         headers=headers).status_code for n in range(11)]
    assert codes == [201] * 10 + [429]
