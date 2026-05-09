from yakoon.base.runtime.errors import DomainError


class InvalidInvocation(DomainError):

    def __init__(
        self,
        message: str,
        code: str = "invalid_invocation",
    ):
        super().__init__(message)

        self.message = message
        self.code = code


class MissingAction(InvalidInvocation):

    def __init__(
        self,
        *,
        command: str,
        supported: list[str],
    ):

        msg = (
            f"Command '{command}' requires an action.\n\n"
            f"Supported actions:\n" + "\n".join(f"- {x}" for x in supported)
        )

        super().__init__(
            msg,
            code="missing_action",
        )


class UnsupportedAction(InvalidInvocation):

    def __init__(
        self,
        *,
        command: str,
        action: str,
        supported: list[str],
    ):

        msg = (
            f"Command '{command}' does not support action '{action}'.\n\n"
            f"Supported actions:\n" + "\n".join(f"- {x}" for x in supported)
        )

        super().__init__(
            msg,
            code="unsupported_action",
        )
