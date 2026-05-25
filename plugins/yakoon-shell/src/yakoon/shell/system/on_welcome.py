from yakoon.base.flow import out
from yakoon.base.nodes import RuntimeContext

from ..ports import OnProject

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_welcome(ctx: RuntimeContext):

    projection = await ctx.ports.get(OnProject)(
        name="welcome/result",
        lang=ctx.session.lang,
        state={"name": ctx.request.payload},
    )

    yield out(projection)
