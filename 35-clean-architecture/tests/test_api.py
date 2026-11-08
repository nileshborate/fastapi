# Integration tests: all layers together - router -> service -> repository -> database
import httpx
import pytest

pytestmark = pytest.mark.anyio


async def add_teachers(api: httpx.AsyncClient) -> None:
    for name in ("Nilesh", "Asha"):
        await api.post("/teachers", json={"name": name})


async def add_course(api: httpx.AsyncClient, title: str, teacher_id: int = 1) -> httpx.Response:
    body = {"title": title, "fee": 299, "teacher_id": teacher_id}
    return await api.post("/courses", json=body)


async def test_create_and_list(api: httpx.AsyncClient) -> None:
    await add_teachers(api)
    response = await add_course(api, "FastAPI Basics")
    assert response.status_code == 201
    assert response.json()["teacher"] == {"id": 1, "name": "Nilesh"}
    assert [c["title"] for c in (await api.get("/courses")).json()] == ["FastAPI Basics"]


async def test_domain_errors_become_http(api: httpx.AsyncClient) -> None:
    await add_teachers(api)
    assert (await add_course(api, "FastAPI Basics", teacher_id=9)).json() == {
        "detail": "Teacher not found"}
    await add_course(api, "FastAPI Basics")
    assert (await add_course(api, "FastAPI Basics")).status_code == 409
    for title in ("Course B", "Course C"):
        await add_course(api, title)
    response = await add_course(api, "Course D")
    assert response.status_code == 422
    assert response.json() == {"detail": "A teacher can teach at most 3 courses"}
    assert (await api.get("/courses/99")).status_code == 404


async def test_transfer(api: httpx.AsyncClient) -> None:
    await add_teachers(api)
    await add_course(api, "FastAPI Basics")
    response = await api.post("/courses/1/transfer", json={"teacher_id": 2})
    assert response.json()["teacher"] == {"id": 2, "name": "Asha"}
    assert (await api.get("/courses/1")).json()["teacher"]["name"] == "Asha"
    again = await api.post("/courses/1/transfer", json={"teacher_id": 2})
    assert again.status_code == 422
