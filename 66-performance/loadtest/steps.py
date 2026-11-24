# homework 66 - step by step: 100, 200, 400, 800 visitors, 30 s each. p95 > 500 ms: where?
#   locust -f loadtest/steps.py --host https://YOUR-DOMAIN --headless --csv steps
from locust import LoadTestShape
from locustfile import Visitor  # noqa: F401 - the SAME visitor (and the pass/fail check)


class Steps(LoadTestShape):
    users = [100, 200, 400, 800]
    seconds = 30

    def tick(self) -> tuple[int, float] | None:
        step = int(self.get_run_time() // self.seconds)
        if step >= len(self.users):
            return None                              # None = the test is over
        return self.users[step], self.users[step] / 10   # (users, new users a second)
