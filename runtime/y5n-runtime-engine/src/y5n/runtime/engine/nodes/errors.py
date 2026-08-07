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


class InvalidOptionError(InvocationError):
    """A declared option was used against its syntactic form.

    E.g. a value given after a flag (``--administrative root``) or a
    value-option used without a value (``--world`` alone). The form is
    part of the command contract (``Param.kind``); ``reason`` carries a
    ready-to-show message.
    """

    def __init__(self, option: str, reason: str, usages: list[dict]):
        self.option = option
        self.reason = reason
        self.usages = usages
