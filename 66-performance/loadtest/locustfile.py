# Video 66 - what ONE visitor does, again and again. Locust starts many of them at once:
#   locust -f loadtest/locustfile.py --host https://YOUR-DOMAIN --headless -u 50 -r 10 -t 60s
import random

from locust import HttpUser, between, events, task


class Visitor(HttpUser):
    wait_time = between(0.5, 1.5)          # a person reads a bit before the next click

    @task(5)                               # 5 of 9 clicks: the course list
    def list_courses(self) -> None:
        self.client.get("/courses")

    @task(3)                               # 3 of 9: one course - name= : ONE line in the report
    def one_course(self) -> None:
        self.client.get(f"/courses/{random.randint(1, 2000)}", name="/courses/{id}")

    @task(1)
    def health(self) -> None:
        self.client.get("/health/ready")


@events.quitting.add_listener
def pass_or_fail(environment, **_kw) -> None:
    """homework 66: a load test that can FAIL - exit code 1 for a script or CI"""
    total = environment.stats.total
    p95 = total.get_response_time_percentile(0.95)
    if p95 > 500 or total.fail_ratio > 0.01:
        print(f"!!! FAILED: p95 {p95} ms (max 500) · {total.fail_ratio:.1%} failed (max 1 %)")
        environment.process_exit_code = 1
    else:
        print(f"OK: p95 {p95} ms · {total.fail_ratio:.1%} failed")
