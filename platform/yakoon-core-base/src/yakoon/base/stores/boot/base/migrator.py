from abc import ABC, abstractmethod
from pathlib import Path


class BaseMigrator(ABC):

    def __init__(self, scripts: Path):
        self.scripts = Path(scripts)

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

    async def _ensure_migration_table(self):
        await self.apply_script("""
            CREATE TABLE IF NOT EXISTS __migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)

    async def _get_applied_versions(self) -> set[str]:
        rows = await self.fetch_all("SELECT version FROM __migrations", ())
        return {r[0] for r in rows}

    async def _record_applied(self, version: str):
        await self.execute("INSERT INTO __migrations (version) VALUES (?)", (version,))

    # abstract low-level DB ops
    @abstractmethod
    async def apply_script(self, sql: str): ...

    @abstractmethod
    async def execute(self, sql: str, params: tuple): ...

    @abstractmethod
    async def fetch_all(self, sql: str, params: tuple) -> list[tuple]: ...
