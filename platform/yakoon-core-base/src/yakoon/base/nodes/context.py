from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from yakoon.base.nodes import Request
    from yakoon.platform.runtime import Session

from .handler import DescriptionHandler, PortsFromHandler
from .ports import NodePorts


@dataclass(slots=True)
class RuntimeContext:  # TODO: später Event?

    request: Request
    session: Session
    ports: NodePorts
    ports_from: PortsFromHandler
    node: DescriptionHandler
    metadata: dict[str, Any] = field(default_factory=dict)
