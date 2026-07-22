"""Adapter: source.read port for the Runtime Bus.

Converts SDK-style ``read(query=..., context=...)`` calls
into the internal ``DataRequest`` and delegates to the registry.
"""

from __future__ import annotations

from typing import Any

from y5n.runtime.engine.runtime.context import Call
from y5n.runtime.engine.sources import DataRequest


class SourceReadAdapter:
    """SDK-facing source.read Port."""

    def __init__(self, registry) -> None:
        self._registry = registry

    async def read(
        self,
        call: Call,
        *,
        query: str,
        context: dict[str, Any] | None = None,
    ) -> Any:
        request = DataRequest(query, context or {})
        return await self._registry.read(request)
