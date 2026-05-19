from yakoon.base.resources import ResourceRef

# ----------------------------------
# RESOURCES
# ----------------------------------


async def get_resource(domain: str, **kwargs):

    lang = kwargs.get("lang")
    scope = kwargs.get("scope")
    key = kwargs.get("key")

    if domain == "manual":
        return ResourceRef(
            package="yakoon.ident",
            path=f"resources/{lang}/manuals/{scope}/man",
        )

    return ResourceRef(
        package="yakoon.ident",
        path=f"resources/{lang}/templates/{scope}/{key}",
    )
