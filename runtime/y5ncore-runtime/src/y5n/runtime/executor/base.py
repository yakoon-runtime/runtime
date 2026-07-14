from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias

from y5n.base.flow.dsl import Outcome
from y5n.base.ports.models import HealthResult

if TYPE_CHECKING:
    from y5n.base.nodes.node import Node
    from y5n.base.nodes.space import NodeSpace

FlowYield: TypeAlias = Outcome | AsyncGenerator | None
RunResult: TypeAlias = AsyncGenerator[FlowYield, Any] | Awaitable[None]


class ExecutorKind(Enum):
    RUNTIME = "runtime"
    SCRIPT = "script"
    PROCESS = "process"


class Phase(Enum):
    SETUP = "setup"
    RUN = "run"


class Executor(Protocol):

    def run(
        self,
        node: Node,
        phase: Phase,
        space: NodeSpace,
    ) -> RunResult: ...


class DiagnosticExecutor(Protocol):
    """Optional protocol for executors that support runtime diagnostics.

    Separate from Executor — not every executor needs health checks.
    """

    async def health(self, node: Node) -> HealthResult: ...


class ExecutorRegistry:

    def __init__(self):
        self._executors: dict[ExecutorKind, Executor] = {}

    def register(self, kind: ExecutorKind, executor: Executor) -> None:
        self._executors[kind] = executor

    def get(self, kind: ExecutorKind) -> Executor:
        return self._executors[kind]
