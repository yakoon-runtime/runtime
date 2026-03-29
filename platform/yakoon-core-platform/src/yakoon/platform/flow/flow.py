from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from yakoon.base.flow.primitives import Control
from yakoon.base.runtime.input import InputEvent

from .cursor import FlowCursor
from .types import FlowKind


@dataclass
class Flow:
    id: str

    command_key: str
    controller_id: str
    request: str
    cursor: FlowCursor
    control: Control | None = None

    pending_value: Any | None = None
    scheduled: bool = False

    wake_at: float | None = None
    kind: FlowKind = FlowKind.USER

    input_queue: deque = field(default_factory=deque)
    input_version: int = 0

    def has_stack(self):
        return bool(self.cursor._stack)

    def push_event(self, data: InputEvent):
        self.input_queue.append((self.input_version, data))

    def pop_event(self) -> InputEvent | None:
        if not self.input_queue:
            return None

        _version, data = self.input_queue.popleft()
        # TODO: _version später für concurrency / ordering
        return data
