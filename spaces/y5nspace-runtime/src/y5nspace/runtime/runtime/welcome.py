from y5n.api.flows import out
from y5n.api.nodes import NodeSpace

from ..ports import OnProject

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    projection = await space.ports.get(OnProject)(
        name="welcome/result",
        lang=space.session.lang,
        state={"name": space.request.payload},
    )

    yield out(projection)
