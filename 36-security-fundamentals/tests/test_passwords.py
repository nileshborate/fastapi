# Hashing: one way, salted, slow
from app.passwords import ITERATIONS, hash_password, verify_password


def test_hash_is_not_the_password() -> None:
    stored = hash_password("admin-pass-123")
    assert "admin-pass-123" not in stored
    assert stored.startswith(f"pbkdf2_sha256${ITERATIONS}$")


def test_same_password_new_salt_new_hash() -> None:
    assert hash_password("admin-pass-123") != hash_password("admin-pass-123")


def test_verify() -> None:
    stored = hash_password("admin-pass-123")
    assert verify_password("admin-pass-123", stored)
    assert not verify_password("admin-pass-124", stored)
