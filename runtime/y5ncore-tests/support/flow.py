from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from y5n.base.nodes import Node
from y5n.base.runtime import Event
from y5n.runtime.flow import Flow, FlowCursor

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from y5n.base.flow.primitives import Outcome
    from y5n.runtime.runtime.sessions.session import Session

    _Handler = Callable[..., AsyncGenerator[Outcome | None, Any]]


def make_flow(
    handler: _Handler,
    *,
    session: Session,
    payload: object = "test",
) -> Flow:
    node = Node(key="test", run=handler)  # type: ignore[arg-type]
    flow = Flow(
        id=uuid4().hex,
        node=node,
        event=Event(payload=payload),
        cursor=FlowCursor("run"),
    )
    session.add_flow(flow)
    return flow
