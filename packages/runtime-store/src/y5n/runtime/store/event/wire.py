import os

from y5n.runtime.store.sequence.settings import SequenceSettings
from y5n.runtime.store.sequence.wire import build_store as build_sequencer

from .runtime import StoreRuntime
from .settings import StorageSettings
from .wires import wire_memory, wire_postgres


def build_store(settings: StorageSettings) -> StoreRuntime:
    if settings.backend == "memory":
        return wire_memory.build_store(settings)

    if settings.backend == "postgres":
        return wire_postgres.build_store(settings)

    raise RuntimeError(f"Invalid storage backend: {settings.backend}")


class EventStoreFactory:
    """Materialize a complete event store from an installation binding.

    The factory owns the config language — the runtime never sees it.
    ``config`` is a dict with an optional ``backend`` (``memory`` or
    ``postgres``, default ``memory``) and an optional ``dsn``. A ``dsn``
    is either a literal connection string or an ``env://NAME`` reference
    to an environment variable holding the connection string.

    The factory builds the entity store *and* its sequencer: sequencing
    is part of the storage semantics (ADR-19).
    """

    def build(self, config=None) -> StoreRuntime:
        backend, dsn = _parse_config(config)
        store_runtime = build_store(StorageSettings(backend=backend, dsn=dsn or ""))
        sequencer = build_sequencer(
            SequenceSettings(backend=backend, dsn=dsn or ""),
        )
        return StoreRuntime(
            objects=store_runtime.objects,
            sequencer=sequencer,
            on_initialize=store_runtime.on_initialize,
            on_shutdown=store_runtime.on_shutdown,
        )


def _parse_config(config):
    """Interpret an opaque factory config as (backend, dsn)."""
    if config is None:
        return "memory", None
    if not isinstance(config, dict):
        raise RuntimeError(
            f"EventStoreFactory config must be a dict, got {type(config).__name__}"
        )
    backend = config.get("backend", "memory")
    if backend not in ("memory", "postgres"):
        raise RuntimeError(f"Unsupported EventStoreFactory backend: {backend!r}")
    dsn = config.get("dsn")
    if dsn is not None:
        dsn = _resolve_dsn(dsn)
    if backend == "postgres" and not dsn:
        raise RuntimeError("EventStoreFactory: backend 'postgres' requires a dsn")
    return backend, dsn


def _resolve_dsn(dsn: str) -> str:
    if dsn.startswith("env://"):
        name = dsn[len("env://") :]
        resolved = os.getenv(name)
        if not resolved:
            raise RuntimeError(
                f"EventStoreFactory: dsn environment variable not set: {name}"
            )
        return resolved
    return dsn
