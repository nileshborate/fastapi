# Background tasks = plain functions. FastAPI runs them AFTER the response is sent.
import time
from datetime import datetime
from pathlib import Path


def write_log(message: str, log_file: Path) -> None:
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {message}"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def send_welcome_email(name: str, email: str, log_file: Path, delay: float) -> None:
    time.sleep(delay)                   # pretend: a slow mail server (a few seconds)
    write_log(f"welcome email sent to {name} <{email}>", log_file)
