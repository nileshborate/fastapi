# The hash helpers - no database
from app.security import hash_password, verify_password


def test_new_salt_every_time() -> None:
    assert hash_password("blue-river-42") != hash_password("blue-river-42")


def test_verify() -> None:
    stored = hash_password("blue-river-42")
    assert verify_password("blue-river-42", stored) == (True, None)
    assert verify_password("blue-river-43", stored) == (False, None)
