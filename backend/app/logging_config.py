"""Logging configuration for the Lessons Hub backend."""

import json
import logging
import os
import sys


class JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def configure_logging() -> None:
    """Configure root logger based on DEPLOYMENT_PROFILE."""
    profile = os.environ.get("DEPLOYMENT_PROFILE", "local")
    cloud_profiles = {"aws", "azure", "gcp"}

    handler = logging.StreamHandler(sys.stderr)
    if profile in cloud_profiles:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s [%(name)s] %(message)s"))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
