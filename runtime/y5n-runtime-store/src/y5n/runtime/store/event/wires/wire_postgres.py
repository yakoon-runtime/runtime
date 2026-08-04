from y5n.runtime.store.event.backends import PostgresBackend
from y5n.runtime.store.event.settings import StorageSettings

from ..runtime import StoreRuntime
from ..store import create_entity_store


def build_store(settings: StorageSettings):

    # ------------------------
    # --- DEFINING BACKEND ---
    # ------------------------

    backend = PostgresBackend(settings.dsn)

    # ---------------------
    # --- BUILDING STORE ---
    # ---------------------

    store = create_entity_store(backend.exec())

    return StoreRuntime(
        objects=store,
        on_initialize=backend.initialize,
        on_shutdown=backend.shutdown,
    )
