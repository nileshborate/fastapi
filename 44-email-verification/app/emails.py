# The two emails we send - the link carries the token, the email carries the link
from datetime import timedelta

from app.config import get_settings
from app.mailer import Email


def verify_email(to: str, token: str) -> Email:
    settings = get_settings()
    link = f"{settings.frontend_url}/verify-email?token={token}"
    return Email(to=to, subject="Confirm your email",
                 body=f"Welcome to Course Hub! Confirm your email:\n{link}\n"
                      f"The link works once, for {settings.verify_link_hours} hours.")


def reset_email(to: str, token: str) -> Email:
    settings = get_settings()
    link = f"{settings.frontend_url}/reset-password?token={token}"
    return Email(to=to, subject="Reset your password",
                 body=f"Somebody asked to reset your password. If it was you:\n{link}\n"
                      f"The link works once, for {settings.reset_link_minutes} minutes.\n"
                      "Not you? Ignore this email - nothing changes.")


def verify_lifetime() -> timedelta:
    return timedelta(hours=get_settings().verify_link_hours)


def reset_lifetime() -> timedelta:
    return timedelta(minutes=get_settings().reset_link_minutes)
