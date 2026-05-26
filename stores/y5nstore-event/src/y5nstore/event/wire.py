from y5nstore.event.settings import StorageSettings

from .runtime import StoreRuntime
from .wires import wire_memory, wire_postgres


def build_store(settings: StorageSettings) -> StoreRuntime:
    if settings.backend == "memory":
        return wire_memory.build_store(settings)

    if settings.backend == "postgres":
        return wire_postgres.build_store(settings)

    raise RuntimeError(f"Invalid storage backend: {settings.backend}")
