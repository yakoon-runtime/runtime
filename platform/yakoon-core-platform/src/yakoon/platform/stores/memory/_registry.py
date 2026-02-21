from yakoon.base.stores.base.registry import StoreRegistry
from yakoon.base.stores.memory.shard import InMemoryShardCounterStore
from yakoon.platform.stores.memory.session import InMemorySessionStore


class MemoryStoreRegistry(StoreRegistry):

    def __init__(self):
        self.sessions = InMemorySessionStore()
        self.counters = InMemoryShardCounterStore()
