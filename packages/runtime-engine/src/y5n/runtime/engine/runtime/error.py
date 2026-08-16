# ----------------------------------------
# NODE ERRORS
# ----------------------------------------


class NodeNotFound(Exception):

    def __init__(
        self,
        command: str,
        suggestions: list[str] | None = None,
    ):
        self.command = command
        self.suggestions = suggestions or []


class NodeNotExecutable(Exception):

    def __init__(self, command: str):
        self.command = command


# ----------------------------------------
# PERMISSION ERRORS
# ----------------------------------------


class PermissionDenied(Exception):
    pass


# ----------------------------------------
# ELEVATION ERRORS
# ----------------------------------------


class ElevationRequired(Exception):
    """The session's security context does not cover a privileged node.

    Permission is not the question here — the account may well have the
    grant. ``privileged`` declares that a conscious confirmation is
    required on top of the permission (elevation). The session security
    context (normal/temporary/administrative) decides whether that
    confirmation is still needed.
    """

    def __init__(self, command: str = ""):
        self.command = command
