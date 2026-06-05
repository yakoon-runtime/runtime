from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from y5n.base.flow.primitives import Control
    from y5n.base.nodes import Node


class Flow(Protocol):
    id: str
    node: Node
    control: Control | None
