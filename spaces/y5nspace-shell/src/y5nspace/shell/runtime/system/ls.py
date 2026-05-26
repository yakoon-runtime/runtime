from y5n.api.data import DataRequest
from y5n.api.flows import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnSourceRead

from ...ports import OnProject

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

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
