from __future__ import annotations

from .allocator import ShardAllocator
from .backends.memory import MemoryShardRepository
from .backends.postgres import PostgresShardRepository
from .runtime import Sequencer
from .settings import SequenceSettings


def build_store(settings: SequenceSettings) -> Sequencer:
    if settings.backend == "memory":
        repo = MemoryShardRepository()
        on_initialize = None
        on_shutdown = None
    elif settings.backend == "postgres":
        repo = PostgresShardRepository(settings.dsn)
        on_initialize = repo.initialize
        on_shutdown = repo.shutdown
    else:
        raise RuntimeError(f"Invalid backend: {settings.backend}")

    allocator = ShardAllocator(repo, range_size=1000)
    return Sequencer(
        allocator,
        on_initialize=on_initialize,
        on_shutdown=on_shutdown,
    )
