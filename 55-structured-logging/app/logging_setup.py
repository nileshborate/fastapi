# Structured logging with the standard library: one JSON object per line
import json
import logging
import logging.config
from contextvars import ContextVar
from datetime import UTC, datetime

from app.config import get_settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

SECRET_KEYS = {"password", "card_number", "token", "authorization"}
# every attribute a LogRecord already has - anything else came in through extra={...}
STANDARD = set(vars(logging.makeLogRecord({}))) | {"message", "asctime", "request_id",
                                                   "color_message"}


class RequestIdFilter(logging.Filter):
    """adds the current request id to EVERY record - you never pass it by hand"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, UTC)
        entry = {
            "ts": ts.isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "service": get_settings().service,
        }
        for key, value in vars(record).items():          # the fields from extra={...}
            if key not in STANDARD:
                entry[key] = "***" if key in SECRET_KEYS else value
        if record.exc_info:
            exc_type, exc, _ = record.exc_info
            entry["exc_type"] = exc_type.__name__ if exc_type else None
            entry["exc_message"] = str(exc)
            entry["traceback"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def setup_logging() -> None:
    settings = get_settings()
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"request_id": {"()": RequestIdFilter}},
        "formatters": {
            "json": {"()": JsonFormatter},
            "plain": {"format": "%(asctime)s %(levelname)-7s %(name)s %(message)s"},
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "stream": "ext://sys.stdout",
                        "formatter": "json" if settings.log_json else "plain",
                        "filters": ["request_id"]},
        },
        "root": {"level": settings.log_level, "handlers": ["console"]},
        "loggers": {                        # uvicorn's own loggers -> through OUR handler
            "uvicorn": {"handlers": [], "propagate": True},
            "uvicorn.error": {"handlers": [], "propagate": True},
            "uvicorn.access": {"handlers": [], "propagate": False},   # we log requests
            "httpx": {"level": "WARNING"},          # chatty libraries: only problems
            "httpcore": {"level": "WARNING"},
            "asyncio": {"level": "WARNING"},
        },
    })
