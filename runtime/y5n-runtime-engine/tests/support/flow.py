from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from y5n.runtime.engine.nodes import Node
from y5n.runtime.api.runtime import Event
from y5n.runtime.engine.flow import Flow, FlowCursor
from y5n.runtime.engine.runtime.invocation import derive_invocation_context

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from y5n.runtime.api.flow.primitives import Pulse
    from y5n.runtime.engine.runtime.sessions.session import Session

    _Handler = Callable[..., AsyncGenerator[Pulse | None, Any]]


def make_flow(
    handler: _Handler,
    *,
    session: Session,
    payload: object = "test",
) -> Flow:
    node = Node(key="test", run=handler)  # type: ignore[arg-type]
    flow_id = session.next_flow_id()
    flow = Flow(
        id=flow_id,
        node=node,
        event=Event(payload=payload),
        cursor=FlowCursor("run"),
        invocation=derive_invocation_context(
            node=node, session=session, flow_id=flow_id
        ),
    )
    session.add_flow(flow)
    return flow
