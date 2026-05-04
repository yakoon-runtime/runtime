import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from yakoon.platform.settings import Settings

logdir = Path("logs")
logdir.mkdir(exist_ok=True)


def file_logger(name, filename, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = RotatingFileHandler(
        logdir / filename,
        maxBytes=5_000_000,
        backupCount=5,
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | session=%(session)s | %(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


settings = Settings()
if settings.logging.log_audits:
    file_logger("yakoon.audit", "audit.log")
if settings.logging.log_security:
    file_logger("yakoon.security", "security.log", logging.WARNING)
if settings.logging.log_errors:
    file_logger("yakoon.error", "error.log", logging.ERROR)
