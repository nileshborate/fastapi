# Docker's HEALTHCHECK runs this INSIDE the container: exit code 0 = healthy, 1 = unhealthy
# (slim images have no curl - but they always have Python)
import sys
import urllib.request

try:
    with urllib.request.urlopen("http://127.0.0.1:8000/health/ready", timeout=2) as response:
        sys.exit(0 if response.status == 200 else 1)
except Exception:
    sys.exit(1)
