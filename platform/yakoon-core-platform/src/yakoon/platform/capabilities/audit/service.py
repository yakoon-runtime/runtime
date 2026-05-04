import logging

from yakoon.platform.settings.logging import LoggingSettings


class AuditLogService:

    def __init__(self, settings: LoggingSettings):
        self.settings = settings
        self._audit = logging.getLogger("yakoon.audit")
        self._error = logging.getLogger("yakoon.error")
        self._warning = logging.getLogger("yakoon.warning")
        self._security = logging.getLogger("yakoon.security")

    def audit(self, message: str):
        if self.settings.log_commands:
            self._audit.info(message)

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

    def security(self, session, obj, action):
        if self.settings.log_security:
            self._security.warning(
                "Permission denied",
                extra={
                    "session": session.key,
                    "object": obj,
                    "action": action,
                },
            )
