from yakoon.base.flow import out
from yakoon.base.nodes import RuntimeContext
from yakoon.base.plugins.ports import OnProject
from yakoon.base.sources import DataRequest, OnDataSource

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_list(ctx: RuntimeContext):

    current_node = ctx.session.get_current_node()

    on_source = ctx.ports.get(OnDataSource)
    result = await on_source(DataRequest(f"system:nodes --scope {current_node}"))

    resource = ctx.resource(
        "overview",
        scope="list",
        lang=ctx.session.lang,
    )

    projection = await ctx.ports.get(OnProject)(
        resource=resource,
        state={"nodes": result.rows},
    )

    yield out(projection)
