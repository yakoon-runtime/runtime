from yakoon.platform.settings import settings


class DefaultAuditLogService:

    async def audit(self, msg: str):
        if settings.logging.log_commands:
            print(f"[AUDIT] {msg}")

    async def error(self, exc: Exception):
        if settings.logging.log_errors:
            import traceback

            print(
                "[ERROR]",
                "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            )

    async def permission(self, session, obj, action):
        if settings.logging.log_permission_denied:
            print(f"[SEC] Denied: {session.key} → {obj} ({action})")
