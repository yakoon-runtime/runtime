from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text

from .ports import JOB_FLOW_GET


async def run(space: NodeSpace):
    if space.request.has_option("current"):
        flow = space.session.foreground_flow  # type: ignore
        if not flow:
            yield out(to_text("No job in foreground."))
            return
        space.session.del_flow(flow)  # type: ignore
        yield out(to_text("Job was stopped."))
        return

    get_flow_by_index = space.ports.get(JOB_FLOW_GET)

    flow, index = get_flow_by_index(
        session=space.session,
        request=space.request,
    )
    if not flow:
        yield out(to_text(f"Job {index} not found."))
        return

    space.session.del_flow(flow)  # type: ignore
    yield out(to_text(f"Job {index} was stopped."))
