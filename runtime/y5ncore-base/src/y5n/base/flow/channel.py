from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .protocol import Flow


class Scope(Enum):
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
    raise ValueError(f"Unknown scope: {scope}")
