from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yakoon.base.nodes import Request
    from yakoon.platform.runtime import Session

from .handler import PortsFromHandler
from .ports import NodePorts


@dataclass(slots=True)
class NodeSpace:

    request: Request
    session: Session
    ports: NodePorts
    ports_from: PortsFromHandler
