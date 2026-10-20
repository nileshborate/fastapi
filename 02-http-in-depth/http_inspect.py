# Video 2 - How the Web Works: HTTP in Depth
# Nilesh Technology - FastAPI Mastery: Zero to Production
#
# Sends HTTP requests and prints every part of the response:
# status line, headers and body. Uses only Python's standard library.
#
# Run:  python http_inspect.py
#       python http_inspect.py https://jsonplaceholder.typicode.com/users/1

import json
import sys
import urllib.error
import urllib.request

BASE = "https://jsonplaceholder.typicode.com"


def show(method, url, body=None):
    print("=" * 70)
    print(f">>> REQUEST:  {method} {url}")

    data = None
    headers = {"Accept": "application/json", "User-Agent": "nilesh-technology-demo"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
        print(f">>> BODY:     {json.dumps(body)}")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            status, reason, res_headers, raw = res.status, res.reason, res.headers, res.read()
    except urllib.error.HTTPError as err:          # 4xx / 5xx still have a response
        status, reason, res_headers, raw = err.code, err.reason, err.headers, err.read()

    print(f"\n<<< STATUS LINE:  HTTP {status} {reason}")
    print("<<< HEADERS:")
    for key in ("Content-Type", "Content-Length", "Date", "Cache-Control"):
        if res_headers.get(key):
            print(f"      {key}: {res_headers.get(key)}")
    print("<<< BODY:")
    try:
        print(json.dumps(json.loads(raw), indent=2))
    except ValueError:
        print(raw.decode("utf-8", errors="replace")[:500])
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        show("GET", sys.argv[1])
    else:
        show("GET", f"{BASE}/posts/1")                                         # read
        show("POST", f"{BASE}/posts", {"title": "Hello", "body": "From Python", "userId": 1})  # create
        show("GET", f"{BASE}/posts/99999")                                     # 404 example
