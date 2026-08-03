from __future__ import annotations

import logging
import sys

from app.core.config import settings


class RequestIDFilter(logging.Filter):
    def __init__(self) -> None:
        super().__init__()
        self._request_id: str | None = None

    @property
    def request_id(self) -> str | None:
        return self._request_id

    @request_id.setter
    def request_id(self, value: str | None) -> None:
        self._request_id = value

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = self._request_id or "-"
        return True


_request_id_filter = RequestIDFilter()


def get_request_id_filter() -> RequestIDFilter:
    return _request_id_filter


def setup_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(settings.log_level.upper())

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(request_id)-36s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    handler.addFilter(_request_id_filter)

    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    logging.getLogger("passlib").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    root_logger.info(
        "Logging configured",
        extra={"environment": settings.environment.value},
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
