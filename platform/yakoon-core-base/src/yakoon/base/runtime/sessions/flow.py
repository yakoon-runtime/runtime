from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class FlowState(Enum):
    READY = auto()
    SLEEPING = auto()
    WAITING_INPUT = auto()


# ============================================================
# Flow
# ============================================================


@dataclass
class Flow:
    command_key: str
    controller_id: str
    request: str
    cursor: FlowCursor
    last_step: Any | None = None
    state: FlowState = FlowState.READY

    input_queue: deque = field(default_factory=deque)
    input_version: int = 0


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


# ============================================================
# Flow Conrroll
# ============================================================


class FlowControl:

    def __init__(self):

        self._pending = 0
        self._ready = asyncio.Event()
        self._ready.set()

    def acquire(self) -> None:

        self._pending += 1

        if self._pending == 1:
            self._ready.clear()
            # print("acquire")

    def try_acquire(self) -> bool:

        if self._pending == 0:
            self.acquire()
            return True

        return False

    def release(self) -> None:

        if self._pending == 0:
            return

        self._pending -= 1

        if self._pending == 0:
            self._ready.set()
            # print("Release")

    async def wait_ready(self) -> None:

        await self._ready.wait()

    def is_ready(self) -> bool:

        return self._pending == 0
