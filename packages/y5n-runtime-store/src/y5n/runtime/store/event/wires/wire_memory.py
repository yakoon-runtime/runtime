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

    return StoreRuntime(objects=store)
