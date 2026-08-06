from __future__ import annotations

from collections.abc import (
    AsyncGenerator,
    Awaitable,
)
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias

from y5n.runtime.api.flow.dsl import Pulse

if TYPE_CHECKING:
    from .node import Node

# ----------------------------------
# RESULT
# ----------------------------------


FlowYield: TypeAlias = Pulse | AsyncGenerator | None
RunResult: TypeAlias = AsyncGenerator[FlowYield, Any] | Awaitable[None]

# ----------------------------------
# HANDLER
# ----------------------------------


class RunHandler(Protocol):
    """A node's run contract — parameterless.

    The handler is ``async def main()``: it reads its whole invocation from
    ``context.current()`` (ADR-12). The engine establishes the invocation
    context before every step; the handler consumes it.
    """

    def __call__(
        self,
    ) -> RunResult: ...


class ResolveHandler(Protocol):
    """Host-side content interpretation.

    ``node`` is the component whose capability is resolved; ``capability``
    names the capability (``man``, ``document``, ...). Returns a ``Resource``
    or an awaitable of one.
    """

    def __call__(
        self,
        *,
        node: Node,
        capability: str,
        parameters: dict[str, Any] | None = None,
    ) -> Any: ...
