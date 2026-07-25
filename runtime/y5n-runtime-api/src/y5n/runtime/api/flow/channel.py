from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, assert_never

if TYPE_CHECKING:
    from .protocol import Flow


class Scope(Enum):
    """Defines event routing scopes.

    FLOW — events are scoped to a single flow (flow.id + channel).
    SESSION — events are visible to all flows in a session.
    USER_INPUT — reserved for user input delivery to the foreground flow.
    """

    FLOW = "flow"
    SESSION = "session"
    USER_INPUT = "user_input"


def resolve(scope: Scope, channel: str, *, flow: Flow | None = None) -> str:
    if scope == Scope.FLOW:
        assert flow is not None, "FLOW scope requires a flow"
        return f"{flow.id}:{channel}"
    elif scope == Scope.SESSION:
        return channel
    elif scope == Scope.USER_INPUT:
        assert flow is not None, "USER_INPUT scope requires a flow"
        return f"{flow.id}:__user__"
    else:
        assert_never(scope)
