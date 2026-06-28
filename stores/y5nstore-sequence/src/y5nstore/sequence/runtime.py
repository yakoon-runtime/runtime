from __future__ import annotations

from typing import Protocol

from .allocator import ShardAllocator


class Sequencer:

    def __init__(
        self,
        allocator: ShardAllocator,
        *,
        on_initialize=None,
        on_shutdown=None,
    ):
        self._allocator = allocator
        self.on_initialize = on_initialize
        self.on_shutdown = on_shutdown

    async def next_id(self, prefix: str) -> str:
        shard = await self._allocator.pick_writable_shard(prefix)
        return str(shard.range_start + shard.value)

    async def initialize(self):
        if self.on_initialize:
            await self.on_initialize()

    async def shutdown(self):
        if self.on_shutdown:
            await self.on_shutdown()


class OnInitialize(Protocol):
    async def __call__(self) -> None: ...


class OnShutdown(Protocol):
    async def __call__(self) -> None: ...
