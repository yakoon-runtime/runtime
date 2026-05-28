from y5n.api.flows import out
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

    assert flow.control

    space.session.set_foreground_flow(flow.id)  # type: ignore
    await flow.control.resume(flow, space.session)
    yield out(to_text(f"Job {index} moved to foreground."))
