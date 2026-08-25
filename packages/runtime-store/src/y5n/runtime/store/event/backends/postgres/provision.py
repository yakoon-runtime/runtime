"""PostgreSQL schema provisioning of the runtime store.

The store's factory owns the schema of the store it materializes (ADR-19:
the factory owns its config language and its storage knowledge).
Provisioning applies the bundled, idempotent DDL to an existing database:

- ``CREATE_STORE_TABLES.sql``    → event store tables
- ``CREATE_STORE_INDEXES.sql``   → event store index
- ``CREATE_SEQUENCE_TABLES.sql`` → sequencer shard table

All PostgreSQL/``asyncpg`` knowledge stays inside the store component —
the tool never sees ``postgresql://``, ``asyncpg`` or the DDL. Neither
databases nor roles are created: provisioning consumes an existing
database the operator created.
"""

from __future__ import annotations

import importlib.resources

from .dsn import target_database

SCHEMA_PACKAGE = "y5n.runtime.store.sql.postgres"
SCHEMA_SCRIPTS = (
    "CREATE_STORE_TABLES.sql",
    "CREATE_STORE_INDEXES.sql",
    "CREATE_SEQUENCE_TABLES.sql",
)


class DatabaseDoesNotExist(RuntimeError):
    """The configured target database cannot be reached.

    A stable, machine-readable signal of the store: ``provision`` failed
    because the target database is missing — not because of any other
    storage problem. ``yak`` offers to create it (an admin operation
    outside the store), then re-provisions.
    """

    def __init__(self, database: str):
        super().__init__(f'database "{database}" does not exist')
        self.database = database


async def provision_postgres_schema(dsn: str) -> None:
    """Apply the bundled schema to the database at ``dsn`` (idempotent).

    Every statement is ``CREATE ... IF NOT EXISTS``, so repeated
    provisioning is safe. The scripts are applied inside one transaction.
    A missing target database surfaces as ``DatabaseDoesNotExist`` — never
    as a raw asyncpg error.
    """
    import asyncpg

    try:
        conn = await asyncpg.connect(dsn)
    except asyncpg.InvalidCatalogNameError as exc:
        raise DatabaseDoesNotExist(target_database(dsn)) from exc
    try:
        async with conn.transaction():
            for name in SCHEMA_SCRIPTS:
                script = (
                    importlib.resources.files(SCHEMA_PACKAGE)
                    .joinpath(name)
                    .read_text(encoding="utf-8")
                )
                await conn.execute(script)
    finally:
        await conn.close()
