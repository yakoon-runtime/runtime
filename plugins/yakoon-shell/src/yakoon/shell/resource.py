from yakoon.base.resources import ResourceRef

# ----------------------------------
# RESOURCES
# ----------------------------------


def get_resource(key: str, **kwargs):

    scope = kwargs.get("scope")
    lang = kwargs.get("lang")

    return ResourceRef(
        package="yakoon.shell",
        path=f"resources/{lang}/templates/{scope}/{key}",
    )
