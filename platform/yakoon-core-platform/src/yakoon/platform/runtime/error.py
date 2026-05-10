from dataclasses import dataclass

from yakoon.base.runtime.errors import BaseError

# ----------------------------------------
# PLATFORM ERRORS
# ----------------------------------------


class PlatformError(BaseError):
    pass


# ----------------------------------------
# PLATFORM ERRORS
# ----------------------------------------


class CommandNotFound(PlatformError):

    NUMBER = 10
    CODE = "command_not_found"

    def __init__(
        self,
        app_id: str,
        command: str,
        suggestions: list[str] | None = None,
    ):
        super().__init__(
            app_id=app_id,
            data={
                "command": command,
                "suggestions": suggestions or [],
            },
            dev_hint=("Command resolution failed after lookup."),
        )


class PermissionDenied(PlatformError):

    NUMBER = 15
    CODE = "permission_denied"

    def __init__(
        self,
        app_id: str,
        permission: str | None = None,
    ):
        super().__init__(
            app_id=app_id,
            data={
                "permission": permission,
            },
            dev_hint=("Permission check failed " "during command invocation."),
        )


# ----------------------------------------
# CRITICAL ERRORS
# ----------------------------------------


@dataclass
class CriticalError(Exception):

    message: str

    code: str | None = None
