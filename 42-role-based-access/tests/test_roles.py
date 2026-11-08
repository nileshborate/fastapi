# Roles come from the database, nobody picks their own, and the database guards them too
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.deps import require_roles
from app.make_admin import make_admin
from app.models import User
from app.roles import Role, has_permission
from tests.conftest import auth


def test_a_new_user_is_a_student(client: TestClient) -> None:
    body = {"email": "x@example.com", "full_name": "Xavier", "password": "blue-river-42"}
    assert client.post("/users", json=body | {"role": "admin"}).status_code == 422
    assert client.post("/users", json=body).json()["role"] == "student"


def test_a_role_change_works_at_once(client: TestClient, users: dict) -> None:
    course = {"title": "Python for Kids", "fee": 99}
    meera = users["student"]                                      # the SAME token all along
    assert client.post("/courses", json=course, headers=meera).status_code == 403
    client.patch("/admin/users/3/role", json={"role": "teacher"}, headers=users["admin"])
    assert client.post("/courses", json=course, headers=meera).status_code == 201


def test_admin_rules(client: TestClient, users: dict) -> None:
    asha = users["admin"]
    response = client.patch("/admin/users/1/role", json={"role": "student"}, headers=asha)
    assert response.status_code == 400
    response = client.patch("/admin/users/3/role", json={"role": "boss"}, headers=asha)
    assert response.status_code == 422                            # not a Role
    response = client.patch("/admin/users/99/role", json={"role": "admin"}, headers=asha)
    assert response.status_code == 404


def test_enroll_once(client: TestClient, users: dict) -> None:
    meera = users["student"]
    client.post("/courses", json={"title": "FastAPI", "fee": 299}, headers=users["teacher"])
    assert client.post("/courses/1/enroll", headers=meera).status_code == 201
    assert client.post("/courses/1/enroll", headers=meera).status_code == 409     # twice
    assert client.post("/courses/9/enroll", headers=meera).status_code == 404


def test_make_admin_script(client: TestClient) -> None:
    auth(client, "asha@example.com")
    assert client.portal.call(make_admin, "nobody@example.com").startswith("no user")
    answer = client.portal.call(make_admin, "asha@example.com")
    assert answer == "asha@example.com is now an admin"


def test_the_database_refuses_an_unknown_role(client: TestClient) -> None:
    auth(client, "asha@example.com")

    async def set_role() -> None:
        async with SessionLocal() as db:
            await db.execute(update(User).values(role="superuser"))
            await db.commit()
    with pytest.raises(IntegrityError):
        client.portal.call(set_role)


def test_the_factory_and_the_map() -> None:
    assert require_roles(Role.ADMIN) is not require_roles(Role.ADMIN)    # a NEW function
    assert has_permission("teacher", "courses:create")
    assert not has_permission("teacher", "courses:delete")
    assert not has_permission("student", "courses:create")
