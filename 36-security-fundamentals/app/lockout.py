# Homework answer (Video 36): block a user's login after 3 wrong passwords in a row
import time

MAX_FAILS = 3
BLOCK_SECONDS = 60

FAILS: dict[str, int] = {}              # username -> wrong passwords in a row
BLOCKED_UNTIL: dict[str, float] = {}    # username -> unix time


def now() -> float:                     # one place for the clock - tests can replace it
    return time.time()


def is_blocked(username: str) -> bool:
    return BLOCKED_UNTIL.get(username, 0) > now()


def record_failure(username: str) -> None:
    FAILS[username] = FAILS.get(username, 0) + 1
    if FAILS[username] >= MAX_FAILS:
        BLOCKED_UNTIL[username] = now() + BLOCK_SECONDS
        FAILS[username] = 0


def record_success(username: str) -> None:
    FAILS.pop(username, None)
