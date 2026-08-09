"""Runtime logging (ADR-17 Phase 4).

After the audit rework, this is no longer an audit trail — the Event
Store records activity and domain events. What remains is *runtime*
logging: warnings and errors that describe the runtime itself (a scheduler
iteration limit, an unhandled exception), not fachliche events.
"""

from __future__ import annotations

import logging
import tomllib
from logging.handlers import RotatingFileHandler
from pathlib import Path

from y5n.runtime.engine.settings import Settings
from y5n.runtime.engine.settings.logging import LoggingSettings


def _resolve_logdir() -> Path:
    """Use context .yak/logs/ if configured, otherwise fall back to settings."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        ctx = parent / ".yak" / "context.toml"
        if not ctx.exists():
            continue
        try:
            with open(ctx, "rb") as f:
                data = tomllib.load(f)
            rel = data.get("logs", {}).get("path", ".yak/logs")
            log = (parent / rel).resolve()
            log.mkdir(parents=True, exist_ok=True)
            return log
        except Exception:
            break

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


def _file_logger(name, filename, level=logging.INFO):
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


_settings = Settings()

if _settings.logging.log_errors:
    _file_logger("error", "y5n.error.log", logging.ERROR)
if _settings.logging.log_warnings:
    _file_logger("warning", "y5n.warning.log", logging.WARNING)


class RuntimeLogService:

    def __init__(self, settings: LoggingSettings):
        self.settings = settings
        self._error = logging.getLogger("error")
        self._warning = logging.getLogger("warning")

    def warning(self, message: str, session):
        if self.settings.log_warnings:
            self._warning.warning(message, extra={"session": session.key})

    def error(self, exc: Exception, session=None):
        if self.settings.log_errors:
            self._error.error(
                "Unhandled exception",
                exc_info=(type(exc), exc, exc.__traceback__),
                extra={"session": session.key if session else None},
            )
