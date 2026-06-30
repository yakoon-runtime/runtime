from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text
from y5n.base.flow.primitives import EmitView, Outcome

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

    # Restore the last persisted interaction view
    # when the flow returns to foreground.
    # Use the target flow's id as job_id so the restored
    # projection replaces the original form group instead of
    # creating a duplicate.
    if flow.view:
        yield Outcome(effects=[EmitView(
            flow.view,
            job_id=flow.id,
            ctx=flow.event.context,
        )])
