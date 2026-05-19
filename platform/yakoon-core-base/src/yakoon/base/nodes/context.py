from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from yakoon.base.commands import Request
    from yakoon.platform.runtime import Session

from .describe import NodeDescription
from .handler import ResourceFromHandler, ResourceHandler
from .ports import NodePorts


@dataclass(slots=True)
class RuntimeContext:  # TODO: später Event?

    ports: NodePorts
    request: Request
    session: Session
    resource: ResourceHandler
    resource_from: ResourceFromHandler
    node: NodeDescription
    metadata: dict[str, Any] = field(default_factory=dict)
