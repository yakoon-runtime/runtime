# ----------------------------------------
# DOMAIN ERROR
# ----------------------------------------


class DomainError(Exception):

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code
