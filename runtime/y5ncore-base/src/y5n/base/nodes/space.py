from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from y5n.base.nodes import NodePath, Request
    from y5n.base.runtime.sessions import Session


from .handler import PortsFromHandler
from .ports import NodePorts


@dataclass(slots=True)
class NodeSpace:
    """Execution context passed to a run handler.

    Provides access to the node path, request, session, ports,
    and pre-assembled resources from the originating node.
    """

    path: NodePath
    request: Request
    session: Session
    ports: NodePorts
    ports_from: PortsFromHandler
    resources: dict[str, dict[str, Path]] | None = None
    """Resource paths from the originating node, keyed by type then variant.
    Populated during command dispatch from the resolved node."""
