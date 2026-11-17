# Run: python -m demos.schedule    - celery beat sends 'heartbeat' every 5 s, a worker runs it
import time

import redis

from demos.common import beat, flush_redis, log, worker


def main() -> None:
    flush_redis()
    store = redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    with worker(), beat():
        log("worker + beat started - waiting 16 s ...")
        time.sleep(16)
    log(f"heartbeats -> {store.lrange('heartbeats', 0, -1)}")
    with open("beat.log") as file:
        sent = [line for line in file if "Sending due task heartbeat" in line]
    log(f"beat.log   -> 'Sending due task heartbeat-every-5-seconds' x {len(sent)}")


main()
