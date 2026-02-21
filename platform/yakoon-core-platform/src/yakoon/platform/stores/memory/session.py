
from yakoon.base.stores.memory.base_store import MemoryStore


class InMemorySessionStore(MemoryStore):
    """
    Domain-specific store for BaseSession objects.
    Currently uses raw MemoryStore behavior.
    Override methods here only if session-specific logic is required.
    """

    def __init__(self):
        super().__init__()
