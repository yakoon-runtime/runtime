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

SCHEMA_PACKAGE = "y5n.runtime.store.sql.postgres"
SCHEMA_SCRIPTS = (
    "CREATE_STORE_TABLES.sql",
    "CREATE_STORE_INDEXES.sql",
    "CREATE_SEQUENCE_TABLES.sql",
)


async def provision_postgres_schema(dsn: str) -> None:
    """Apply the bundled schema to the database at ``dsn`` (idempotent).

    Every statement is ``CREATE ... IF NOT EXISTS``, so repeated
    provisioning is safe. The scripts are applied inside one transaction.
    """
    import asyncpg

    conn = await asyncpg.connect(dsn)
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
