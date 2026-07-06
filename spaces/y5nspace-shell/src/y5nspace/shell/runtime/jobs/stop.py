from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text

from .ports import OnFlowGetByIndex


async def run(space: NodeSpace):

    get_flow_by_index = space.ports.get(OnFlowGetByIndex)

    flow, index = get_flow_by_index(
        session=space.session,
        request=space.request,
    )
    if not flow:
        yield out(to_text(f"Job {index} not found."))
        return

    space.session.del_flow(flow)  # type: ignore
    yield out(to_text(f"Job {index} was stopped."))
