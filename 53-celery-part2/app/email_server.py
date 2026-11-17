# A FLAKY email server: it fails the first few times for each address - like a real network
import time

from app.config import get_settings

attempts: dict[str, int] = {}                     # address -> how many times we tried


class EmailServerDown(ConnectionError):
    """temporary: try again later"""


def send(to: str, subject: str) -> int:
    if "@" not in to or to.startswith("bounce"):
        raise ValueError(f"invalid address: {to}")                 # permanent: never retry
    attempts[to] = attempts.get(to, 0) + 1
    time.sleep(get_settings().email_seconds)
    if to.startswith("down") or attempts[to] <= get_settings().email_fail_times:
        raise EmailServerDown(f"SMTP timeout ({to}, attempt {attempts[to]})")
    return attempts[to]
