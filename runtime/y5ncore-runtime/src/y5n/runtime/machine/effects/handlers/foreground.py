from typing import cast

from y5n.base.flow.primitives import Effect, Foreground
from y5n.runtime.flow import Flow
from y5n.runtime.runtime import Session


class ForegroundHandler:
    """Handles Foreground: marks the flow as the session's foreground flow.

    The foreground flow receives user input by default.  When no
    flow_id is given the current flow is used.
    """

    async def execute(self, effect: Effect, session: Session, flow: Flow) -> None:
        e = cast(Foreground, effect)
        flow_id = e.flow_id or flow.id
        session.set_foreground_flow(flow_id)
