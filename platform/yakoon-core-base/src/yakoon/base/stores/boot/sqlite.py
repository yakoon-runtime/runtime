import pathlib

import aiosqlite

from yakoon.base.stores.boot.base.migrator import BaseMigrator


class SqliteMigrator(BaseMigrator):

    def __init__(self, db: aiosqlite.Connection, scripts: pathlib.Path):
        self.db = db
        self.scripts = scripts

    async def run(self):
        await self._ensure_migration_table()
        applied = await self._get_applied_versions()

        for file in sorted(self.scripts.glob("V*.sql")):
            version = file.stem.split("__")[0]
            if version in applied:
                continue

            sql = file.read_text(encoding="utf-8")
            await self.apply_script(sql)
            await self._record_applied(version)

    async def apply_script(self, sql: str):
        await self.db.executescript(sql)
        await self.db.commit()

    async def execute(self, sql: str, params: tuple):
        await self.db.execute(sql, params)
        await self.db.commit()

    async def fetch_all(self, sql: str, params: tuple) -> list[tuple]:
        cursor = await self.db.execute(sql, params)
        rows = await cursor.fetchall()
        return [tuple(row) for row in rows]
