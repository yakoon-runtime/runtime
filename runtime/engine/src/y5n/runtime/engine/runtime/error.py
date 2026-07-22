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


class NodeNotRunnable(Exception):
    pass


# ----------------------------------------
# PERMISSION ERRORS
# ----------------------------------------


class PermissionDenied(Exception):
    pass
