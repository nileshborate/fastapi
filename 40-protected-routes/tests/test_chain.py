# The demo as a test: the dependency chain runs in order, get_db only ONCE per request
from demos import chain


def test_order_and_cache() -> None:
    assert chain.calls == ["get_token", "get_db: open", "get_current_user",
                           "get_current_active_user", "the endpoint",
                           "get_db: close (after the answer)"]
