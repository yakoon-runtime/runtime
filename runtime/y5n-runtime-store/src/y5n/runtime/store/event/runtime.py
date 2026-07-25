from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Protocol

from .store import EntityStore


class StoreRuntime:

    def __init__(
        self,
        objects: EntityStore,
        begin_transaction,
        on_initialize: Oninitialize | None = None,
        on_shutdown: OnShutdown | None = None,
    ):
        self.objects = objects
        self._begin_transaction = begin_transaction
        self.on_initialize = on_initialize
        self.on_shutdown = on_shutdown

    # --------------------
    # --- TRANSACTIONS ---
    # --------------------

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[EntityStore]:
        async with self._begin_transaction() as tx_store:
            yield tx_store

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
