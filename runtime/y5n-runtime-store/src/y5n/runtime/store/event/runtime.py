from __future__ import annotations

from typing import Protocol

from .store import EntityStore


class StoreRuntime:

    def __init__(
        self,
        objects: EntityStore,
        on_initialize: Oninitialize | None = None,
        on_shutdown: OnShutdown | None = None,
    ):
        self.objects = objects
        self.on_initialize = on_initialize
        self.on_shutdown = on_shutdown

    # -----------------
    # --- LIFECYCLE ---
    # -----------------

    async def initialize(self):
        if self.on_initialize:
            await self.on_initialize()

    async def shutdown(self):
        if self.on_shutdown:
            await self.on_shutdown()


# ----------------------------------
# PORTS
# ----------------------------------


class Oninitialize(Protocol):
    async def __call__(self) -> None: ...


class OnShutdown(Protocol):
    async def __call__(self) -> None: ...
