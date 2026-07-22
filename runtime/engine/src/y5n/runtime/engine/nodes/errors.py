# ----------------------------------------
# INVOCATION ERRORS
# ----------------------------------------


class InvocationError(Exception):
    """Base class for invocation validation errors."""


class UsageError(InvocationError):

    def __init__(self, usages: list[dict], command: str | None = None):
        self.usages = usages
        self.command = command


class UnknownOptionsError(InvocationError):

    def __init__(
        self,
        unknown_options: list[str],
        valid_options: list[str],
        usages: list[dict],
    ):
        self.unknown_options = unknown_options
        self.valid_options = valid_options
        self.usages = usages
