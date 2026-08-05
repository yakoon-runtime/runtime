"""Adapter: ``runtime.resource`` port for the Runtime Bus.

Coordinates content resolution per ADR-10. The service resolves a node's
capability through the node's host — it finds the node, follows its ``host:``
path, and delegates to the host node's ``resolve`` handler. The runtime never
knows which host it is.

* ``resolve(node_path, capability, parameters=None)`` → a ``Resource``
* ``supports(node_path, capability)`` → bool
"""

from __future__ import annotations

from typing import Any

from y5n.runtime.api.runtime.invoke import Call
from y5n.runtime.engine.resources.host import find_host, resolve_via_host


class ResourceAdapter:
    """SDK-facing ``runtime.resource.resolve`` / ``supports`` Port."""

    def __init__(self, tree) -> None:
        self._tree = tree

    def _node(self, call: Call, node_path: str | None):
        path = node_path or call.caller_path
        if not path:
            return None
        return self._tree.find(path)

    async def resolve(
        self,
        call: Call,
        *,
        node_path: str | None,
        capability: str,
        parameters: dict[str, Any] | None = None,
    ):
        node = self._node(call, node_path)
        if node is None:
            raise LookupError(f"node not found: {node_path or call.caller_path}")
        return await resolve_via_host(self._tree, node, capability, parameters or {})

    async def supports(
        self,
        call: Call,
        *,
        node_path: str | None,
        capability: str,
    ) -> bool:
        node = self._node(call, node_path)
        if node is None:
            return False
        host = find_host(self._tree, node)
        return (
            host is not None
            and host.resolve is not None
            and bool((node.resources or {}).get(capability))
        )
