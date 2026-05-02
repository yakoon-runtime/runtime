from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from .store import EntityStore


class StoreRuntime:

    def __init__(self, objects: EntityStore, begin_transaction):
        self.objects = objects
        self._begin_transaction = begin_transaction

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[EntityStore]:
        async with self._begin_transaction() as tx_store:
            yield tx_store
