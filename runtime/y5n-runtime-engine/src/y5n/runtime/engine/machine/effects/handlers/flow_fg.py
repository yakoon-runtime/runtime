from typing import cast

from y5n.runtime.api.flow.primitives import (
    Effect,
    FlowFgEffect,
    Suspend,
    YieldToScheduler,
)
from y5n.runtime.engine.flow import Flow
from y5n.runtime.engine.runtime import Session


class FlowFgHandler:
    """Handles FlowFgEffect: brings a flow to the foreground.

    Suspended flows are resumed, the flow becomes the session's
    foreground flow, and its last persisted view is re-projected
    (restoring the interactive form after jobs/bg + jobs/fg).
    """

    def __init__(self, on_projection):
        self._on_projection = on_projection

    async def execute(self, effect: Effect, session: Session, flow: Flow) -> None:
        e = cast(FlowFgEffect, effect)
        flow_id = e.flow_id or flow.id
        target = session.get_flow(flow_id)
        if not target:
            return

        if isinstance(target.control, Suspend):
            target.control = YieldToScheduler()

        session.set_foreground_flow(flow_id)

        if target.view:
            await self._on_projection(
                session=session,
                document=target.view,
                ctx=target.event.context,
                job_id=target.id,
                mode="replace",
            )
