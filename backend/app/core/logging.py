import json
import logging
import sys
import time
from typing import Any, Dict, Optional
import uuid
from contextvars import ContextVar

# Context variables for request tracing
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

class JSONFormatter(logging.Formatter):
    """Custom JSON structured formatter for SatQuery AI operations."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get() or getattr(record, "request_id", None),
        }

        # Include structured extra fields if present
        for key in ["image_id", "operation", "status", "duration_ms", "file_format", "size_bytes"]:
            val = getattr(record, key, None)
            if val is not None:
                log_data[key] = val

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up structured logging."""
    root_logger = logging.getLogger("satquery")
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        root_logger.addHandler(handler)

    # Disable excessive noise from 3rd party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("rasterio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return root_logger

logger = logging.getLogger("satquery")
