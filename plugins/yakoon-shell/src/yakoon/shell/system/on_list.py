from yakoon.base.flow import out
from yakoon.base.nodes import RuntimeContext
from yakoon.base.sources import DataRequest, OnSourceRead

from ..ports import OnProject

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_list(ctx: RuntimeContext):

    current_node = ctx.session.get_current_node()

    on_source = ctx.ports.get(OnSourceRead)
    result = await on_source(DataRequest(f"system:nodes --scope {current_node}"))

    navigables = [x for x in result.rows if x["navigable"]]

    projection = await ctx.ports.get(OnProject)(
        name="list/overview",
        lang=ctx.session.lang,
        state={
            "nodes": result.rows,
            "navigables": navigables,
        },
    )

    yield out(projection)
