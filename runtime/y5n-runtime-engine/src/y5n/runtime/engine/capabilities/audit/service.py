"""Runtime logging (ADR-17 Phase 4).

After the audit rework, this service is no longer an audit trail — the
Event Store records activity and domain events. What remains is *runtime*
logging: warnings and errors that describe the runtime itself (a scheduler
iteration limit, an unhandled exception), not fachliche events.
"""

import logging

from y5n.runtime.engine.settings.logging import LoggingSettings


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
