"""
Logging utility.

Responsibility:
    Provides a pre-configured logger for the entire application.
    All modules should import `logger` from here rather than
    configuring their own logging — ensures consistent format
    and a single place to adjust log level / handlers.

Future extension points:
    - Add structured JSON logging for production
    - Integrate with external observability (e.g. Sentry, Datadog)
    - Add request-id correlation via middleware context
"""

import logging
import sys

from app.core.config import settings


def _build_logger() -> logging.Logger:
    """Create and configure the application logger."""
    log = logging.getLogger(settings.APP_NAME)
    log.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    log.addHandler(handler)
    return log


logger = _build_logger()
