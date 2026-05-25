from yakoon.base.flow import out
from yakoon.base.naming import Key
from yakoon.base.nodes import Request, RuntimeContext

from ..ports import OnProject

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_whoami(ctx: RuntimeContext):

    yield await _handler(
        identity=ctx.session.get_identity(),
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
    )


# ----------------------------------
# HANDLER
# ----------------------------------


async def _handler(
    *,
    identity: Key | None,
    request: Request,
    on_project: OnProject,
):

    if identity:

        projection = await on_project(
            name="whoami/show",
            lang=request.lang,
            state={
                "user": str(identity),
            },
        )

    else:

        projection = await on_project(
            name="whoami/hint",
            lang=request.lang,
        )

    return out(projection)
