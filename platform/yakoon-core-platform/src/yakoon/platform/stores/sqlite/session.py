
from yakoon.base.stores.sqlite.base_store import SQLiteStore


class SQLiteSessionStore(SQLiteStore):

    def __init__(self, db_path: str):
        super().__init__(db_path=db_path, table_name="sessions")

    async def get_by_token(self, token: str) -> dict | None:
        sessions = await self.fetch_by_fields(token=token, limit=1)
        return sessions[0] if sessions else None

    async def expire_all(self) -> None:
        sessions = await self.fetch_by_fields()
        for session in sessions:
            session["active"] = False
            await self.save(session)
