from yakoon.base.stores.base.registry import StoreRegistry
from yakoon.base.stores.sqlite.shard import SQLiteShardCounterStore
from yakoon.platform.stores.sqlite.session import SQLiteSessionStore


class SQLiteStoreRegistry(StoreRegistry):

    def __init__(self, db_path="yakoon.db"):
        self.sessions = SQLiteSessionStore(db_path)
        self.counters = SQLiteShardCounterStore(db_path)
