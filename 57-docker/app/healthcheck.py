# Docker's HEALTHCHECK runs this INSIDE the container: exit code 0 = healthy, 1 = unhealthy
# (slim images have no curl - but they always have Python)
# Homework 57: the logic lives in check(), so a test can call it with any URL
import sys
import urllib.request

URL = "http://127.0.0.1:8000/health/ready"


def check(url: str = URL, timeout: float = 2) -> int:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 0 if response.status == 200 else 1
    except Exception:  # 503 (HTTPError), connection refused, timeout ...
        return 1


if __name__ == "__main__":
    sys.exit(check())
