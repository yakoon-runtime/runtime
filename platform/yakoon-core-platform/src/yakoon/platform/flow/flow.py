from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from yakoon.base.flow.primitives import Control
from yakoon.base.runtime import InputEvent

from .cursor import FlowCursor
from .types import FlowKind

DEFAULT = "default"


@dataclass
class Flow:
    id: str

    command_key: str
    controller_id: str
    request: str
    cursor: FlowCursor
    control: Control | None = None

    scheduled: bool = False

    wake_at: float | None = None
    kind: FlowKind = FlowKind.USER

    inbox: dict[str, deque] = field(default_factory=lambda: defaultdict(deque))

    def has_stack(self):
        return bool(self.cursor._stack)

    def has_mail(self, channel: str = DEFAULT):
        return bool(self.inbox[channel])

    def push_event(self, event: InputEvent, channel: str = DEFAULT):
        if not isinstance(event, InputEvent):
            raise TypeError("push_event expects InputEvent")

        self.inbox[channel].append(event)

    def pop_event(self, channel: str = DEFAULT) -> InputEvent | None:
        if not self.inbox[channel]:
            return None
        return self.inbox[channel].popleft()
