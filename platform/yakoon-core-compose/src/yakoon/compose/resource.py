from yakoon.base.resources import ResourceRef
from yakoon.platform.runtime.error import NodeNotFound

# ----------------------------------
# RESOURCES
# ----------------------------------
PACKAGE = "yakoon.platform"

errors = {
    NodeNotFound: "command/not_found.sam",
}


def get_resource(key: type, **kwargs):

    part = errors.get(key)
    lang = kwargs.get("lang")

    return ResourceRef(
        package="yakoon.platform",
        path=f"templates/{lang}/{part}",
    )
