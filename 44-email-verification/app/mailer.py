# Sending emails - behind ONE small interface, so tests and demos can swap it
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Email:
    to: str
    subject: str
    body: str


class Mailer(Protocol):
    def send(self, email: Email) -> None: ...


class ConsoleMailer:
    """development: keeps every email in a list (and prints it) instead of sending it"""

    def __init__(self) -> None:
        self.outbox: list[Email] = []

    def send(self, email: Email) -> None:
        self.outbox.append(email)
        print(f"[mail] to={email.to} subject={email.subject!r}")


mailer = ConsoleMailer()        # production: an SMTP or an email-API mailer with .send()


def get_mailer() -> Mailer:
    return mailer
