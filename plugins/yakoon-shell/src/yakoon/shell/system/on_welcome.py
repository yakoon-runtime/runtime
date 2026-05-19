from yakoon.base.flow import out
from yakoon.base.nodes import RuntimeContext
from yakoon.base.plugins.ports import OnProject

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_welcome(ctx: RuntimeContext):

    resource = await ctx.resource(
        domain="resource",
        scope="welcome",
        key="result",
        lang=ctx.session.lang,
    )

    projection = await ctx.ports.get(OnProject)(
        resource=resource,
        state={"name": ctx.request.payload},
    )

    yield out(projection)
