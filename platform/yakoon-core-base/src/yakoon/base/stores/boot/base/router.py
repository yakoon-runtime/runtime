import os
import pathlib
from collections.abc import Mapping

import aiosqlite

from yakoon.base.stores.boot.base.migrator import BaseMigrator
from yakoon.base.stores.boot.sqlite import SqliteMigrator


class MigratorRouter:

    def __init__(self, config: Mapping[str, dict]):
        self.config = config

    async def run(self):

        async def _run_migator(migrator: BaseMigrator):
            # print(f"Running migration for '{domain}'")
            await migrator.run()

        for _, cfg in self.config.items():
            backend = cfg["backend"]
            script_path = pathlib.Path(cfg["script_path"])

            if backend == "sqlite":
                db_path = cfg["db_path"]
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                db = await aiosqlite.connect(db_path)
                await _run_migator(SqliteMigrator(db, script_path))

            elif backend == "postgres":
                # pool = await asyncpg.create_pool(cfg["dsn"])
                # _run_migator(PostgresMigrator(pool, schema_root=self.schema_root))
                raise NotImplementedError(backend)

            else:
                raise ValueError(f"Unsupported backend: {backend}")
