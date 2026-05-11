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
    APP_ID = "System"
    CODE = "command_not_found"  # ==> Code sollte IMMER DEFINIERT werden müssen.
    # -> Dazu gibt es eine Datei error_codes.py

    # error_codes.py
    # GROUP_NOT_FOUND = "group_not_found"
    # INVALID_TYPE = "invalid_type"
    # PERMISSION_DENIED = "permission_denied"

    def __init__(
        self,
        command: str,
        suggestions: list[str] | None = None,
        code: str | None = None,
    ):
        super().__init__(
            code=code,
            data={
                "command": command,
                "suggestions": suggestions or [],
            },
            dev_hint=("Command resolution failed after lookup."),
        )


class PermissionDenied(PlatformError):

    NUMBER = 15
    APP_ID = "System"
    CODE = "permission_denied"

    def __init__(
        self,
        permission: str | None = None,
    ):
        super().__init__(
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
