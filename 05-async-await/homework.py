# Video 5 - HOMEWORK
# This program checks 3 students' results. It takes about 3 seconds.
# 1. Convert it to async:  async def, await asyncio.sleep(1), asyncio.gather
# 2. Make it finish in about 1 second.
# The answer is shared at the start of Video 6.

import time


def get_result(student: str) -> str:
    time.sleep(1)   # pretend this calls the university server
    return f"{student}: PASS"


def main() -> None:
    start = time.perf_counter()
    for student in ["Asha", "Ravi", "Meera"]:
        print(get_result(student))
    print(f"Done in {time.perf_counter() - start:.1f}s")


main()
