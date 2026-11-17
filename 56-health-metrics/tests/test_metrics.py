# Metrics: counters by route TEMPLATE, a histogram, a business counter, /metrics itself
from collections.abc import Callable

from fastapi.testclient import TestClient

Metric = Callable[..., float]
TOTAL = "http_requests_total"


def test_requests_are_counted_by_route_template(client: TestClient, metric: Metric) -> None:
    before = metric(TOTAL, method="GET", route="/reports/{course_id}", status="200")
    client.get("/reports/1")
    client.get("/reports/2")                              # two urls - ONE series
    assert metric(TOTAL, method="GET", route="/reports/{course_id}", status="200") == before + 2


def test_unknown_urls_share_one_label(client: TestClient, metric: Metric) -> None:
    before = metric(TOTAL, method="GET", route="unmatched", status="404")
    client.get("/random/abc")
    client.get("/wp-admin.php")
    assert metric(TOTAL, method="GET", route="unmatched", status="404") == before + 2


def test_a_crash_is_counted_as_500(client: TestClient, metric: Metric) -> None:
    before = metric(TOTAL, method="GET", route="/boom", status="500")
    assert client.get("/boom").status_code == 500
    assert metric(TOTAL, method="GET", route="/boom", status="500") == before + 1


def test_the_latency_histogram(client: TestClient, metric: Metric) -> None:
    labels = {"method": "GET", "route": "/reports/{course_id}"}
    count = metric("http_request_duration_seconds_count", **labels)
    fast = metric("http_request_duration_seconds_bucket", le="0.25", **labels)
    client.get("/reports/3")                              # ~300 ms
    assert metric("http_request_duration_seconds_count", **labels) == count + 1
    assert metric("http_request_duration_seconds_bucket", le="0.25", **labels) == fast
    assert metric("http_requests_in_progress") == 0


def test_a_business_metric(client: TestClient, metric: Metric) -> None:
    before = metric("enrollments_total", course="2")
    client.post("/enrollments/2")
    client.post("/enrollments/9")                         # 404 - not an enrollment
    assert metric("enrollments_total", course="2") == before + 1
    assert metric("enrollments_total", course="9") == 0


def test_the_metrics_endpoint(client: TestClient, metric: Metric) -> None:
    before = metric(TOTAL, method="GET", route="/health/live", status="200")
    client.get("/health/live")
    response = client.get("/metrics")
    assert response.headers["content-type"].startswith("text/plain")
    assert "# TYPE http_requests_total counter" in response.text
    assert metric(TOTAL, method="GET", route="/health/live", status="200") == before == 0
