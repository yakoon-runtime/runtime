from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias

from y5n.runtime.engine.flow.dsl import Outcome
from y5n.runtime.engine.ports.models import HealthResult

"""
ABI — Application Binary Interface.

Every Yakoon executable is an application. The Runtime does not know
how to run applications — it delegates this to an Executor.

The Executor defines the ABI: the contract between the Runtime and
the application code.

  Runtime → Executor → Application

Each Executor kind implements a different ABI:

  runtime   async def run(space)          in-process, full platform API
  python    def main()                    in-process, synchronous (batch)
  script    python3 app.py → stdout       subprocess, isolated
  process   _yak/run/app (shebang)        subprocess, any language

The ABI is the answer to: "How does this application want to be run?"

NOTE: The python executor (batch) is NOT the same as the old PythonExecutor
with ThreadPool + runpy. It loads the module via importlib, calls main()
synchronously, and captures stdout via redirect_stdout. No thread pool,
no 20ms pump — it runs once and yields all output at once.

The runtime executor (async) remains the primary host for Yakoon services.
It runs async generators in the scheduler, supports millions of concurrent
flows, foreground/background, and wait-states.
"""


if TYPE_CHECKING:
    from y5n.runtime.engine.nodes.node import Node
    from y5n.runtime.engine.nodes.space import NodeSpace

FlowYield: TypeAlias = Outcome | AsyncGenerator | None
RunResult: TypeAlias = AsyncGenerator[FlowYield, Any] | Awaitable[None]


class ExecutorKind(Enum):
    RUNTIME = "runtime"
    PYTHON = "python"
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
