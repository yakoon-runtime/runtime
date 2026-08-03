from contextlib import asynccontextmanager

from y5n.runtime.store.event.settings import StorageSettings

from ..backends.memory import MemoryBackend
from ..runtime import StoreRuntime
from ..store import create_entity_store


def build_store(settings: StorageSettings) -> StoreRuntime:

    # ------------------------
    # --- DEFINING BACKEND ---
    # ------------------------

    backend = MemoryBackend()

    # ---------------------
    # --- BUILDING STORE ---
    # ---------------------

    store = create_entity_store(backend)

    # -----------------------------------
    # --- BUILDING TRANSAKTIONS STORE ---
    # -----------------------------------

    @asynccontextmanager
    async def begin_transaction():
        async with backend.transaction() as tx:
            yield create_entity_store(tx)

    return StoreRuntime(
        objects=store,
        begin_transaction=begin_transaction,
    )
