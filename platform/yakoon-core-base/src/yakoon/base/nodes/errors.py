# ----------------------------------------
# USAGE ERROR
# ----------------------------------------


class UsageError(Exception):

    def __init__(self, usages: list[dict]):
        self.usages = usages


class UnknowOptionsError(Exception):

    def __init__(
        self,
        unknown_options: list[str],
        valid_options: list[str],
        usages: list[dict],
    ):
        self.unknown_options = unknown_options
        self.valid_options = valid_options
        self.usages = usages
