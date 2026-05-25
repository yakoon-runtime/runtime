from yakoon.base.flow import out
from yakoon.base.nodes import RuntimeContext
from yakoon.base.nodes.path import NodePath
from yakoon.base.sources import (
    DataRequest,
    OnSourceRead,
)

from ..ports import OnProject


async def on_man(ctx: RuntimeContext):

    key = ctx.request.arg(0)

    current_node = ctx.session.get_current_node()

    # ----------------------------------
    # Resolve visible nodes
    # ----------------------------------

    on_source = ctx.ports.get(OnSourceRead)

    result = await on_source(DataRequest(f"system:nodes --scope {current_node}"))
    found = next((x for x in result.rows if x["key"] == key), None)

    # ----------------------------------
    # Node not found
    # ----------------------------------

    if not found:

        projection = await ctx.ports.get(OnProject)(
            name="man/error",
            lang=ctx.session.lang,
            state={
                "key": key,
            },
        )

        yield out(projection)
        return

    # ----------------------------------
    # Resolve manual
    # ----------------------------------
    ports = ctx.ports_from(
        path=NodePath.from_string("."),
        absolute=False,
    )

    resource = await ctx.resource_from(
        path=NodePath.from_string("."),
        absolute=False,
        scope=key,
        domain=found["help_domain"],
        lang=ctx.session.lang,
    )

    # ----------------------------------
    # Manual missing
    # ----------------------------------

    if not resource:

        projection = await ctx.ports.get(OnProject)(
            name="man/missing",
            lang=ctx.session.lang,
            state={
                "key": key,
            },
        )

        yield out(projection)
        return

    # ----------------------------------
    # Render manual
    # ----------------------------------

    projection = await ctx.ports.get(OnProject)(
        resource=resource,
        state={
            "node": found,
        },
    )

    yield out(projection)
