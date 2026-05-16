from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .context import RuntimeContext
from .types import NodeKind, NodeScope, NodeVisibility

RunHandler = Callable[[RuntimeContext], Any]  #  Awaitable[None]]


@dataclass(slots=True)
class Node:

    key: str
    name: str | None = None

    # ----------------------------------
    # EXECUTION METADATA
    # ----------------------------------

    kind: NodeKind = NodeKind.USER
    scope: NodeScope = NodeScope.NODE
    visibility: NodeVisibility = NodeVisibility.NORMAL
    is_shell: bool = False

    # ----------------------------------
    # PERMISSIONS
    # ----------------------------------

    anonymous: bool = False

    # ----------------------------------
    # HANDLER
    # ----------------------------------

    run: RunHandler | None = None
    setup: RunHandler | None = None

    # ----------------------------------
    # FIELDS
    # ----------------------------------

    parent: Node | None = None
    children: dict[str, Node] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # ----------------------------------
    # CHILDREN
    # ----------------------------------

    def add(self, container: Node) -> None:
        container.parent = self
        self.children[container.key] = container

    def get(self, key: str) -> Node | None:
        return self.children.get(key)

    # ----------------------------------
    # EXECUTION
    # ----------------------------------

    def has_run(self) -> bool:
        return self.run is not None

    def has_setup(self) -> bool:
        return self.setup is not None

    def walk(self, on_walk: Callable[[Node], None]):
        on_walk(self)
        for child in self.children.values():
            child.walk(on_walk)
