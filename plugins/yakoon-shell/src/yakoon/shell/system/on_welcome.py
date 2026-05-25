from yakoon.base.flow import out
from yakoon.base.nodes import NodeSpace

from ..ports import OnProject

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_welcome(space: NodeSpace):

    projection = await space.ports.get(OnProject)(
        name="welcome/result",
        lang=space.session.lang,
        state={"name": space.request.payload},
    )

    yield out(projection)
