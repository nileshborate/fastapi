# Every request, sent by every role: guest · student · teacher · admin
import pytest
from fastapi.testclient import TestClient

ROLES = ["guest", "student", "teacher", "admin"]
MATRIX = [
    ("GET", "/courses", None, (200, 200, 200, 200)),
    ("POST", "/courses", {"title": "SQL Basics", "fee": 199}, (401, 403, 201, 201)),
    ("PATCH", "/courses/1", {"fee": 349}, (401, 403, 200, 200)),        # Ravi's course
    ("PATCH", "/courses/2", {"fee": 249}, (401, 403, 403, 200)),        # Asha's course
    ("POST", "/courses/1/enroll", None, (401, 201, 403, 403)),
    ("GET", "/admin/users", None, (401, 403, 403, 200)),
    ("PATCH", "/admin/users/3/role", {"role": "student"}, (401, 403, 403, 200)),
    ("DELETE", "/courses/1", None, (401, 403, 403, 204)),
]


@pytest.mark.parametrize(("method", "url", "body", "expected"), MATRIX)
def test_matrix(client: TestClient, users: dict, method: str, url: str, body, expected):
    ravi, asha = users["teacher"], users["admin"]
    client.post("/courses", json={"title": "FastAPI Basics", "fee": 299}, headers=ravi)  # id 1
    client.post("/courses", json={"title": "Docker Basics", "fee": 399}, headers=asha)   # id 2
    codes = tuple(client.request(method, url, json=body, headers=users[role]).status_code
                  for role in ROLES)
    assert codes == expected
