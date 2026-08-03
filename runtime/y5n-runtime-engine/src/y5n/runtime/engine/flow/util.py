"""Shared flow helpers."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from y5n.runtime.api.flow.dsl import Pulse


def empty_flow() -> AsyncGenerator[Pulse, None]:
    """A no-op flow: yields a single Pulse and finishes."""

    async def _noop():
        yield Pulse()

    return _noop()
