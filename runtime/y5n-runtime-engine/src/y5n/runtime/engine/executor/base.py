from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias

from y5n.runtime.api.flow.dsl import Pulse

"""
ABI — Application Binary Interface.

Every Yakoon executable is an application. The Runtime does not know
how to run applications — it delegates this to an Executor.

The Executor defines the ABI: the contract between the Runtime and
the application code.

  Runtime → Executor → Application

The runtime executor runs async generators in the scheduler, supports
millions of concurrent flows, foreground/background, and wait-states.
It remains the primary way Yakoon services are executed.
"""


if TYPE_CHECKING:
    from y5n.runtime.engine.nodes.node import Node

FlowYield: TypeAlias = Pulse | AsyncGenerator | None
RunResult: TypeAlias = AsyncGenerator[FlowYield, Any] | Awaitable[None]


class ExecutorKind(Enum):
    RUNTIME = "runtime"


class Phase(Enum):
    SETUP = "setup"
    RUN = "run"


class Executor(Protocol):

    def run(
        self,
        node: Node,
        phase: Phase,
    ) -> RunResult: ...


class ExecutorRegistry:

    def __init__(self):
        self._executors: dict[ExecutorKind, Executor] = {}

    def register(self, kind: ExecutorKind, executor: Executor) -> None:
        self._executors[kind] = executor

    def get(self, kind: ExecutorKind) -> Executor:
        return self._executors[kind]
