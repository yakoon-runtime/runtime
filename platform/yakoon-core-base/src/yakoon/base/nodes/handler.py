from __future__ import annotations

from collections.abc import (
    AsyncGenerator,
    Awaitable,
)
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias

from yakoon.base.flow.dsl import Outcome

if TYPE_CHECKING:
    from .context import RuntimeContext
    from .path import NodePath


# ----------------------------------
# RESULT
# ----------------------------------


RunResult: TypeAlias = AsyncGenerator[Outcome | None, Any] | Awaitable[None]

# ----------------------------------
# HANDLER
# ----------------------------------


class RunHandler(Protocol):

    def __call__(
        self,
        ctx: RuntimeContext,
    ) -> RunResult: ...


class ResourceHandler(Protocol):

    async def __call__(
        self,
        *,
        domain: Any,
        **kwargs: Any,
    ) -> Any: ...


class ResourceFromHandler(Protocol):

    async def __call__(
        self,
        *,
        path: NodePath,
        absolute: bool,
        domain: Any,
        **kwargs: Any,
    ) -> Any: ...
