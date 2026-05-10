from dataclasses import dataclass


@dataclass
class PlatformError(Exception):

    message: str

    code: str | None = None


# ----------------------------------------
# PLATFORM ERRORS
# ----------------------------------------


class CommandNotFound(PlatformError):

    def __init__(
        self,
        command: str,
        suggestions: list[str] | None = None,
    ):

        self.command = command
        self.suggestions = suggestions or []

        msg = f"Command '{command}' not found"
        if self.suggestions:

            if len(self.suggestions) == 1:
                msg += f"\n\nDid you mean " f"'{self.suggestions[0]}'?"

            else:
                joined = "\n".join(f"  {x}" for x in self.suggestions)
                msg += "\n\nDid you mean:\n\n" f"{joined}"

        super().__init__(
            message=msg,
            code="command_not_found",
        )


class PermissionDenied(PlatformError):

    def __init__(
        self,
    ):

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
