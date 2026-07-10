from y5n.api.dsl import out, view
from y5n.api.nodes import NodeSpace

from ..ports import OnProject

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    projection = await space.ports.get(OnProject)(
        name="system/welcome",
        lang=space.session.lang,
        state={"name": space.request.payload},
    )

    yield view(clear=True)
    yield out(projection)
