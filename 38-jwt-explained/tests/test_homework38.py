# Homework answer (Video 38): a name claim, /token/info, RS256 from another key
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.jwt_tokens import TokenError, decode_access_token
from tests.conftest import ASHA, login


def test_name_comes_from_the_token(client: TestClient) -> None:
    token = login(client, *ASHA).json()["access_token"]
    assert decode_access_token(token)["name"] == "Asha"
    me = client.get("/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["name"] == "Asha"


def test_token_info_reads_without_checking(client: TestClient) -> None:
    fake = jwt.encode({"sub": "1", "role": "admin"}, "z" * 40, algorithm="HS256")
    info = client.get("/token/info", headers={"Authorization": f"Bearer {fake}"}).json()
    assert info["claims"]["role"] == "admin"            # it shows a FAKE token too
    assert info["verified"] is False
    assert client.get("/me", headers={"Authorization": f"Bearer {fake}"}).status_code == 401


def test_rs256_token_from_another_key_is_refused() -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode({"sub": "2", "role": "admin"}, key, algorithm="RS256")
    with pytest.raises(TokenError, match="alg value is not allowed"):
        decode_access_token(token)                      # we only accept HS256
