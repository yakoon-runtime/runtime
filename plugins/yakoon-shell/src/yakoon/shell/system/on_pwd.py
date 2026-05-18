from yakoon.base.flow import out
from yakoon.base.nodes import RuntimeContext
from yakoon.base.projection.model.model import to_text

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_pwd(ctx: RuntimeContext):

    path = ctx.session.get_current_node()
    yield out(to_text("\n" + str(path)))
