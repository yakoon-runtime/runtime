from yakoon.base.flow import out
from yakoon.base.naming import Key
from yakoon.base.nodes import Request, ResourceHandler, RuntimeContext
from yakoon.base.plugins.ports import OnProject

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_whoami(ctx: RuntimeContext):

    yield await _handler(
        identity=ctx.session.get_identity(),
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        resource=ctx.resource,
    )


# ----------------------------------
# HANDLER
# ----------------------------------


async def _handler(
    *,
    identity: Key | None,
    request: Request,
    on_project: OnProject,
    resource: ResourceHandler,
):

    if identity:

        reference = await resource(
            domain="resource",
            scope="whoami",
            key="show",
            lang=request.lang,
        )

        projection = await on_project(
            resource=reference,
            state={
                "user": str(identity),
            },
        )

    else:

        reference = await resource(
            domain="resource",
            scope="whoami",
            key="hint",
            lang=request.lang,
        )

        projection = await on_project(
            resource=reference,
        )

    return out(projection)
