from yakoon.base.stores.sqlite.base_store import SQLiteStore


class SQLiteAccountStore(SQLiteStore):

    def __init__(self, db_path: str):
        super().__init__(db_path=db_path, table_name="accounts")
