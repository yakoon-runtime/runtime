from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yakoon.base.runtime.commands import StepOutcome

# ============================================================
# Flow State
# ============================================================


class FlowState(IntEnum):
    RUNNING = 1
    WAITING = 2
    FINISHED = 3


class TickResult:
    def __init__(self, state: FlowState, outcome: StepOutcome | None):
        self.state = state
        self.outcome = outcome


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
