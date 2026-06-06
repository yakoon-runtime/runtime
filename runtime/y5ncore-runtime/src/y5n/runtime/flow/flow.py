from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from y5n.base.flow.primitives import Control
from y5n.base.runtime import Event

if TYPE_CHECKING:
    from y5n.base.nodes import Node

from .cursor import FlowCursor
from .types import FlowKind

DEFAULT = "default"


@dataclass
class Flow:
    id: str

    node: Node
    event: Event
    cursor: FlowCursor
    tokens: list[str] | None = None
    control: Control | None = None
    view: Any | None = None

    scheduled: bool = False
    wake_at: float | None = None
    kind: FlowKind = FlowKind.USER

    pipeline: list[str] | None = None

    inbox: dict[str, deque] = field(default_factory=lambda: defaultdict(deque))

    def has_stack(self):
        return bool(self.cursor._stack)

    def has_mail(self, channel: str = DEFAULT):
        return bool(self.inbox[channel])

    def push_event(self, event: Event, channel: str = DEFAULT):
        if not isinstance(event, Event):
            raise TypeError("push_event expects Event")

        self.inbox[channel].append(event)

    def pop_event(self, channel: str = DEFAULT) -> Event | None:
        if not self.inbox[channel]:
            return None
        return self.inbox[channel].popleft()
