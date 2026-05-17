from yakoon.base.commands.errors import UnknowOptionsError, UsageError
from yakoon.base.resources import ResourceRef
from yakoon.platform.runtime import NodeNotFound, PermissionDenied, UnhandledError

# ----------------------------------
# PACKAGE
# ----------------------------------

PACKAGE = "yakoon.platform"

# ----------------------------------
# ERRORS
# ----------------------------------

errors = {
    UnhandledError: "error.sam",
    NodeNotFound: "command/not_found.sam",
    UsageError: "command/usage.sam",
    UnknowOptionsError: "command/unknown_options.sam",
    PermissionDenied: "permissions/denied.sam",
}

# ----------------------------------
# HANDLER
# ----------------------------------


def get_resource(key: type, **kwargs):

    part = errors.get(key)
    lang = kwargs.get("lang")

    return ResourceRef(
        package="yakoon.platform",
        path=f"templates/{lang}/{part}",
    )
