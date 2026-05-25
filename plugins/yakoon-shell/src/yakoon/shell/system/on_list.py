from yakoon.api.data import DataRequest
from yakoon.api.flows import out
from yakoon.api.nodes import NodeSpace
from yakoon.api.ports import OnSourceRead

from ..ports import OnProject

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_list(space: NodeSpace):

    current_node = space.session.get_current_node()

    on_source = space.ports.get(OnSourceRead)
    result = await on_source(DataRequest(f"system:nodes --scope {current_node}"))

    navigables = [x for x in result.rows if x["navigable"]]

    projection = await space.ports.get(OnProject)(
        name="list/overview",
        lang=space.session.lang,
        state={
            "nodes": result.rows,
            "navigables": navigables,
        },
    )

    yield out(projection)
