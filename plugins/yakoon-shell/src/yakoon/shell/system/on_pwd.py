from yakoon.base.flow import out
from yakoon.base.nodes import RuntimeContext
from yakoon.base.projection import to_text
from yakoon.base.runtime.errors import DomainError

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_pwd(ctx: RuntimeContext):

    raise DomainError("Test")

    path = ctx.session.get_current_node()
    yield out(to_text("\n" + str(path)))
