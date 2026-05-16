# ----------------------------------------
# INTERNAL ERROR
# ----------------------------------------


class UnhandledError(Exception):
    pass


# ----------------------------------------
# PLATFORM ERRORS
# ----------------------------------------


class PlatformError(Exception):
    pass


# ----------------------------------------
# COMMAND ERRORS
# ----------------------------------------


class CommandNotFound(PlatformError):
    pass


# ----------------------------------------
# PERMISSION ERRORS
# ----------------------------------------


class PermissionDenied(PlatformError):
    pass
