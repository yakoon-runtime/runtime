import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from y5n.runtime.settings import Settings

settings = Settings()

logdir = Path(settings.logging.log_dir).expanduser()
logdir.mkdir(parents=True, exist_ok=True)


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


if settings.logging.log_audits:
    file_logger("audit", "y5n.audit.log")
if settings.logging.log_security:
    file_logger("security", "y5n.security.log", logging.WARNING)
if settings.logging.log_errors:
    file_logger("error", "y5n.error.log", logging.ERROR)
