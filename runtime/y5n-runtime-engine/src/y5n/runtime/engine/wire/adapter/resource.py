"""Adapter: ``runtime.resource`` port for the Runtime Bus.

Exposes resource resolution to the SDK as ordinary service calls:

* ``resolve(ref, parameters=None, node_path=None)`` → a ``Resource``
* ``supports(ref)`` → bool

Per ADR-10 the host implements resolution behind the service; the resolver is
the in-process Python host. ``node_path`` (fallback: the caller's node) gives
``file:`` references their base directory.
"""

from __future__ import annotations

from typing import Any

from y5n.runtime.api.runtime.context import Call


class ResourceAdapter:
    """SDK-facing ``runtime.resource.resolve`` / ``supports`` Port."""

    def __init__(self, resolver, tree) -> None:
        self._resolver = resolver
        self._tree = tree

    async def resolve(
        self,
        call: Call,
        *,
        ref: str,
        parameters: dict[str, Any] | None = None,
        node_path: str | None = None,
    ):
        base = self._base_path(node_path or call.caller_path)
        return await self._resolver.resolve(
            ref,
            parameters=parameters or {},
            base=base,
        )

    async def supports(self, call: Call, *, ref: str) -> bool:
        return self._resolver.supports(ref)

    def _base_path(self, node_path: str | None):
        if node_path is None:
            return None
        node = self._tree.find(node_path)
        return node.fs_path if node is not None else None
