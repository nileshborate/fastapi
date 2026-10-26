# Run:  pytest -v
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100        # a tiny fake PNG


@pytest.fixture(autouse=True)
def temp_upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)   # don't write into the project folder


def test_headers_are_read() -> None:
    response = client.get("/whoami", headers={"User-Agent": "my-app/1.0", "Accept-Language": "en-IN"})
    assert response.json() == {"user_agent": "my-app/1.0", "accept_language": "en-IN"}


def test_api_key_missing_wrong_and_right() -> None:
    assert client.get("/reports").status_code == 422
    assert client.get("/reports", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/reports", headers={"x-api-key": main.API_KEY}).status_code == 200


def test_response_header() -> None:
    assert client.get("/courses").headers["cache-control"] == "public, max-age=60"


def test_cookie_set_read_delete() -> None:
    response = client.post("/preferences/theme", params={"theme": "dark"})
    assert "theme=dark" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
    assert client.get("/preferences").json() == {"theme": "dark"}      # the client sends it back
    client.delete("/preferences/theme")
    assert client.get("/preferences").json() == {"theme": "light"}     # default again


def test_login_form() -> None:
    response = client.post("/login", data={"username": "asha", "password": "secret123"})
    assert response.json() == {"message": "Welcome, asha!"}


def test_login_with_json_fails() -> None:
    response = client.post("/login", json={"username": "asha", "password": "secret123"})
    assert response.status_code == 422


def test_contact_form_model() -> None:
    data = {"name": "Asha", "email": "asha@example.com", "message": "Please add a Django course"}
    assert client.post("/contact", data=data).status_code == 200
    data["email"] = "not-an-email"
    assert client.post("/contact", data=data).status_code == 422


def test_file_as_bytes() -> None:
    response = client.post("/files/size", files={"file": ("notes.txt", b"hello world")})
    assert response.json() == {"size": 11}


def test_upload_thumbnail_ok(tmp_path: Path) -> None:
    response = client.post(
        "/courses/1/thumbnail",
        files={"file": ("cover.png", PNG, "image/png")},
        data={"alt_text": "FastAPI logo"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["original_name"] == "cover.png"
    assert body["saved_as"].endswith(".png")
    assert (tmp_path / body["saved_as"]).read_bytes() == PNG


def test_upload_wrong_type() -> None:
    response = client.post("/courses/1/thumbnail", files={"file": ("virus.exe", b"MZ...", "application/octet-stream")})
    assert response.status_code == 415


def test_upload_too_large() -> None:
    big = b"0" * (main.MAX_IMAGE_SIZE + 1)
    response = client.post("/courses/1/thumbnail", files={"file": ("big.png", big, "image/png")})
    assert response.status_code == 413


def test_multiple_files() -> None:
    files = [("files", ("a.pdf", b"12345", "application/pdf")), ("files", ("b.pdf", b"123", "application/pdf"))]
    assert client.post("/materials", files=files).json() == [{"name": "a.pdf", "size": 5}, {"name": "b.pdf", "size": 3}]
