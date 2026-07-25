from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from y5n.runtime.api.nodes import Invocation, InvocationInput, Node
    from y5n.runtime.api.runtime.sessions import Session


class OnPrepareInput(Protocol):
    """Provides initial values for an invocation before form rendering.

    Returns None when no pre-filled values exist (e.g. on add).
    """

    async def __call__(
        self,
        *,
        node: Node,
        invocation: Invocation,
        tokens: list[str],
        session: Session,
    ) -> InvocationInput | None: ...
