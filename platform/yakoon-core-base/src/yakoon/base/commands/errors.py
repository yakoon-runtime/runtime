from yakoon.base.runtime.errors import DomainError

# ----------------------------------------
# INVALID INVOCATION ERROR
# ----------------------------------------


class InvalidInvocation(DomainError):
    pass


# ----------------------------------------
# MISSING ACTION ERROR
# ----------------------------------------


class MissingAction(InvalidInvocation):
    pass


# ----------------------------------------
# UNSUPPORTED ACTION ERROR
# ----------------------------------------


class UnsupportedAction(InvalidInvocation):
    pass


# ----------------------------------------
# USAGE ERROR
# ----------------------------------------


class UsageError(InvalidInvocation):
    pass


class UnknowOptionsError(InvalidInvocation):
    pass
