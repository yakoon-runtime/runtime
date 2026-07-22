from __future__ import annotations

from collections.abc import (
    AsyncGenerator,
    Awaitable,
)
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias

from y5n.runtime.engine.flow.dsl import Outcome

if TYPE_CHECKING:
    from .path import NodePath
    from .ports import NodePorts
    from .space import NodeSpace

# ----------------------------------
# RESULT
# ----------------------------------


FlowYield: TypeAlias = Outcome | AsyncGenerator | None
RunResult: TypeAlias = AsyncGenerator[FlowYield, Any] | Awaitable[None]

# ----------------------------------
# HANDLER
# ----------------------------------


class RunHandler(Protocol):

    def __call__(
        self,
        space: NodeSpace,
        /,
    ) -> RunResult: ...


class PortsFromHandler(Protocol):

    def __call__(
        self,
        path: NodePath,
        *,
        absolute: bool = False,
    ) -> NodePorts | None: ...
