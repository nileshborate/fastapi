# Video 3 - REST API Fundamentals
# Nilesh Technology - FastAPI Mastery: Zero to Production
#
# Sends all five main HTTP methods to a practice REST API and prints the result.
# Uses only Python's standard library - nothing to install.
#
# Run:  python rest_methods.py
# Note: JSONPlaceholder fakes the writes, so data does not really change.

import json
import urllib.error
import urllib.request

BASE = "https://jsonplaceholder.typicode.com"


def call(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Accept": "application/json", "User-Agent": "nilesh-technology-demo"}
    if data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            status, reason, raw = res.status, res.reason, res.read()
    except urllib.error.HTTPError as err:
        status, reason, raw = err.code, err.reason, err.read()
    text = raw.decode("utf-8", errors="replace").strip()
    short = (text[:70] + "...") if len(text) > 70 else text
    print(f"{method:<7} {path:<12} -> {status} {reason:<10} {short.replace(chr(10), ' ')}")


if __name__ == "__main__":
    call("GET", "/posts/1")                                                          # read one
    call("POST", "/posts", {"title": "FastAPI", "body": "REST demo", "userId": 1})   # create
    call("PUT", "/posts/1", {"id": 1, "title": "Replaced", "body": "All fields", "userId": 1})  # replace
    call("PATCH", "/posts/1", {"title": "Only the title"})                           # partial update
    call("DELETE", "/posts/1")                                                       # delete
