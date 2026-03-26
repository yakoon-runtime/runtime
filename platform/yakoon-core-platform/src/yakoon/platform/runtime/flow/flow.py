from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from yakoon.base.runtime.flow import FlowKind, FlowState
from yakoon.base.runtime.input import InputEvent
from yakoon.base.runtime.steps.controls import Control

from .cursor import FlowCursor


@dataclass
class Flow:
    id: str

    command_key: str
    controller_id: str
    request: str
    cursor: FlowCursor
    control: Control

    state: FlowState = FlowState.READY
    wake_at: float | None = None
    kind: FlowKind = FlowKind.USER

    input_queue: deque = field(default_factory=deque)
    input_version: int = 0

    def push_event(self, data: InputEvent):
        self.input_queue.append((self.input_version, data))

    def pop_event(self) -> InputEvent | None:
        if not self.input_queue:
            return None

        _version, data = self.input_queue.popleft()
        # TODO: _version später für concurrency / ordering
        return data
