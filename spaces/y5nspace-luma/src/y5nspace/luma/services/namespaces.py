from __future__ import annotations

from typing import Protocol

from y5n.api.naming import Namespace


class WorldNamespaces(Protocol):

    def world_namespace(self) -> Namespace: ...
