from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from yakoon.base.commands import Request
from yakoon.base.plugins import ModulePorts

if TYPE_CHECKING:
    from yakoon.platform.runtime import Session

    from .node import Node


@dataclass(slots=True)
class RuntimeContext:

    ports: ModulePorts
    request: Request
    session: Session | None = None
    node: Node | None = None

    # ----------------------------------
    # HELPERS
    # ----------------------------------

    def port(self, cls):
        return self.ports.on_get_port(cls)
