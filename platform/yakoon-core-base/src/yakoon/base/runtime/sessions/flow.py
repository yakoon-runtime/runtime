from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from yakoon.base.host.events import InputEvent


class FlowKind(StrEnum):
    USER = "user"  # sichtbare Jobs
    SYSTEM = "system"  # interne Flows (z.B. jobs, assistant intern)


class FlowState(StrEnum):
    READY = "READY"
    SLEEPING = "SLEEPING"
    WAITING_INPUT = "WAITING_INPUT"


# ============================================================
# Flow
# ============================================================


@dataclass
class Flow:
    id: str  # = field(default_factory=lambda: uuid4().hex)
    command_key: str
    controller_id: str
    request: str
    cursor: FlowCursor
    last_step: Any | None = None
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


# ============================================================
# Flow Cursor
# ============================================================


class FlowCursor:

    def __init__(self, flow_factory):
        self.flow_factory = flow_factory
        self.iterator = None

    def start(self, command, session, request):
        self.iterator = self.flow_factory(command, session, request)

    async def next(self, command, session, request):
        if not self.iterator:
            self.start(command, session, request)
        return await anext(self.iterator)

    async def send(self, value):
        if not self.iterator:
            raise RuntimeError("Cursor not started")
        return await self.iterator.asend(value)
