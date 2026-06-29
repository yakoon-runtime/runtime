from __future__ import annotations

from y5n.base.nodes import Node
from y5n.runtime.runtime import Session


class Interactor:
    """Pipeline stage between node resolution and execution.

    Pass-through by default.  A later step will inspect
    ``session.interaction`` and delegate to a Renderer
    (e.g. ``FormRenderer``) when user input is missing.
    """

    async def intercept(
        self,
        node: Node,
        tokens: list[str],
        session: Session,
    ) -> tuple[Node, list[str]]:
        return node, tokens
