# ----------------------------------------
# PLATFORM ERRORS
# ----------------------------------------


class PlatformError(Exception):
    pass


# ----------------------------------------
# NODE ERRORS
# ----------------------------------------


class NodeNotFound(PlatformError):
    pass


class NodeNotRunnable(PlatformError):
    pass


# ----------------------------------------
# PERMISSION ERRORS
# ----------------------------------------


class PermissionDenied(PlatformError):
    pass
