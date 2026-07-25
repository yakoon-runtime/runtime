from __future__ import annotations

from typing import TYPE_CHECKING

from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.runtime import Event

if TYPE_CHECKING:
    from y5n.runtime.engine.flow import Flow
    from y5n.runtime.engine.runtime.sessions.session import Session


def push_event(
    session: Session,
    scope: Scope,
    channel: str,
    payload: object,
    *,
    flow: Flow | None = None,
) -> None:
    session.push_event(
        scope,
        channel,
        Event(payload=payload),
        flow=flow,
    )
