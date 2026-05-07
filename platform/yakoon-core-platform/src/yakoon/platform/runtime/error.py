from dataclasses import dataclass


@dataclass
class PlatformError(Exception):
    message: str
    code: str | None = None


# ----------------------------------------
# PLATFORM ERRORS
# ----------------------------------------


class CommandNotFound(PlatformError):
    def __init__(self, command: str):
        super().__init__(
            message=f"Command '{command}' not found",
            code="command_not_found",
        )


class PermissionDenied(PlatformError):
    def __init__(self):
        super().__init__(
            message="Permission denied",
            code="permission_denied",
        )


# ----------------------------------------
# CRITICAL ERRORS
# ----------------------------------------


@dataclass
class CriticalError(Exception):
    message: str
    code: str | None = None
