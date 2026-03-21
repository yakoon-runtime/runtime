from dataclasses import dataclass


@dataclass
class PlatformError(Exception):
    message: str
    code: str | None = None


# ----------------------------------------
# COMMAND
# ----------------------------------------


class CommandNotFound(PlatformError):
    def __init__(self, command: str):
        super().__init__(
            message=f"Command '{command}' not found",
            code="command_not_found",
        )


# ----------------------------------------
# PERMISSIONS
# ----------------------------------------


class PermissionDenied(PlatformError):
    def __init__(self):
        super().__init__(
            message="Permission denied",
            code="permission_denied",
        )
