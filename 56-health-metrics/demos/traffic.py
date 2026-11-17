# Send real traffic, read GET /metrics like Prometheus does - and answer questions from it
import asyncio
import time

from prometheus_client.parser import text_string_to_metric_families

from demos.common import serve

PLAN = ["/courses"] * 40 + [f"/reports/{n}" for n in (1, 2, 3)] * 5 + ["/boom"] * 3 + \
       ["/nope/1", "/nope/2"]


async def main() -> None:
    async with serve() as client:
        start = time.perf_counter()
        await asyncio.gather(*(client.get(url) for url in PLAN))
        await asyncio.gather(*(client.post(f"/enrollments/{n}") for n in (2, 2, 2, 1)))
        elapsed = time.perf_counter() - start
        text = (await client.get("/metrics")).text

    print("--- GET /metrics (our lines) ---")
    for line in text.splitlines():
        if line.startswith(("http_requests_total", "enrollments_total",
                            "# TYPE http_requests_total", "http_requests_in_progress")):
            print(line)
        if line.startswith("http_request_duration_seconds") and "/reports/" in line:
            print(line)

    samples = [s for fam in text_string_to_metric_families(text) for s in fam.samples]
    total = sum(s.value for s in samples if s.name == "http_requests_total")
    errors = sum(s.value for s in samples if s.name == "http_requests_total"
                 and s.labels["status"].startswith("5"))
    print("\n--- questions ---")
    print(f"requests: {total:.0f} in {elapsed:.2f} s = {total / elapsed:.0f} per second")
    print(f"error rate (5xx): {errors:.0f} / {total:.0f} = {errors / total:.1%}")
    for route in ("/courses", "/reports/{course_id}"):
        b = [(float(s.labels["le"]), s.value) for s in samples
             if s.name == "http_request_duration_seconds_bucket"
             and s.labels["route"] == route]
        n = max(v for _, v in b)
        p95 = min(le for le, v in b if v >= 0.95 * n)
        sum_ = next(s.value for s in samples if s.name == "http_request_duration_seconds_sum"
                    and s.labels["route"] == route)
        avg_ms = sum_ / n * 1000
        print(f"{route:<22} n={n:.0f}  avg={avg_ms:.0f} ms  p95 <= {p95 * 1000:.0f} ms")


asyncio.run(main())
