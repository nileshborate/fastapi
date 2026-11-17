# Docker's HEALTHCHECK runs this INSIDE the container: exit code 0 = healthy, 1 = unhealthy
# (slim images have no curl - but they always have Python)
import sys
import urllib.error
import urllib.request

URL = "http://127.0.0.1:8000/health/ready"


def check(url: str = URL, timeout: float = 2) -> int:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 0 if response.status == 200 else 1
    except urllib.error.HTTPError as exc:  # a 503 arrives as an exception ...
        exc.close()                        # ... holding an open connection: close it
        return 1
    except OSError:                        # connection refused, timeout
        return 1


if __name__ == "__main__":
    sys.exit(check())
