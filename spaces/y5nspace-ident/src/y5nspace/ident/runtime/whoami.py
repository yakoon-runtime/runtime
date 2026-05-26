from y5n.base.flow import out
from y5n.base.naming import Key
from y5n.base.nodes import NodeSpace, Request

from ..ports import OnProject

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    yield await _handler(
        identity=space.session.get_identity(),
        request=space.request,
        on_project=space.ports.get(OnProject),
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
