from typing import cast

from y5n.runtime.api.flow.primitives import Effect, FlowStopEffect
from y5n.runtime.engine.flow import Flow
from y5n.runtime.engine.runtime import Session


class FlowStopHandler:
    """Handles FlowStopEffect: removes a flow from the session."""

    async def execute(self, effect: Effect, session: Session, flow: Flow) -> None:
        e = cast(FlowStopEffect, effect)
        target = session.get_flow(e.flow_id)
        if target:
            session.del_flow(target)
