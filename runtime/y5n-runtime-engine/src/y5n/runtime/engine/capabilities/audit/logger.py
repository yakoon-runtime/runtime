import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from y5n.runtime.engine.settings import Settings


def _resolve_logdir() -> Path:
    """Use .yak/logs/ if a context is detected, otherwise fall back to settings."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".yak" / "context.toml").exists() or (parent / ".yak" / "state.toml").exists():
            log = parent / ".yak" / "logs"
            log.mkdir(parents=True, exist_ok=True)
            return log
    settings = Settings()
    d = Path(settings.logging.log_dir).expanduser()
    d.mkdir(parents=True, exist_ok=True)
    return d


logdir = _resolve_logdir()


class _SafeFormatter(logging.Formatter):
    """Formatter that substitutes missing keys with empty string."""

    def format(self, record):
        record.__dict__.setdefault("session", "")
        return super().format(record)


def file_logger(name, filename, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = RotatingFileHandler(
        logdir / filename,
        maxBytes=5_000_000,
        backupCount=5,
    )

    formatter = _SafeFormatter(
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
