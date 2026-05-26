from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from y5n.base.nodes import NodePath, Request
    from y5n.base.runtime.sessions import Session


from .handler import PortsFromHandler
from .ports import NodePorts


@dataclass(slots=True)
class NodeSpace:

    path: NodePath
    request: Request
    session: Session
    ports: NodePorts
    ports_from: PortsFromHandler
