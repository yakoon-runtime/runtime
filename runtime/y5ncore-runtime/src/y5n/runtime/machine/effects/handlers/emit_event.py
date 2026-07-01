from typing import cast

from y5n.base.flow.primitives import Effect, EmitEvent
from y5n.runtime.flow import Flow
from y5n.runtime.runtime import Session


class EmitEventHandler:
    """Handles EmitEvent: pushes an event onto a channel.

    The event is delivered to any flow waiting on the given channel
    and scope (FLOW, SESSION, or USER_INPUT).
    """

    async def execute(self, effect: Effect, session: Session, flow: Flow) -> None:
        e = cast(EmitEvent, effect)
        session.push_event(e.scope, e.channel, e.event, flow=flow)
