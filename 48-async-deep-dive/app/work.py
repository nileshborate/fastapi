# Two kinds of slow work - and they need DIFFERENT fixes
import threading
import time


def thread_name() -> str:
    return threading.current_thread().name          # who is running this code right now?


def slow_report(seconds: float) -> str:
    """I/O-bound + BLOCKING: an old library, a sync database driver, requests.get(...)"""
    time.sleep(seconds)                              # the thread waits - it can do nothing else
    return f"report ready after {seconds}s"


def count_primes(limit: int) -> int:
    """CPU-bound: pure Python math - the CPU is busy the whole time"""
    count = 0
    for n in range(2, limit):
        if all(n % d for d in range(2, int(n**0.5) + 1)):
            count += 1
    return count
