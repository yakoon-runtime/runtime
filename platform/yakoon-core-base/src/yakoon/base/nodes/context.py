from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from yakoon.base.commands import Request
    from yakoon.platform.runtime import Session

from .ports import NodePorts
from .resource import ResourceHandler


@dataclass(slots=True)
class RuntimeContext:

    ports: NodePorts
    request: Request
    session: Session
    resource: ResourceHandler
    metadata: dict[str, Any] = field(default_factory=dict)
