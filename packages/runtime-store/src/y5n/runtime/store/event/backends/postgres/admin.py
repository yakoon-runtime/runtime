"""PostgreSQL database-level administration of the runtime store.

Separate from schema provisioning: ``EventStoreFactory.provision()`` owns
the store's schema inside an existing database; this module owns the
*infrastructure* step a tool needs before that — ensuring the target
database exists. All PostgreSQL/``asyncpg`` knowledge lives here: DSN
parsing, the maintenance connection, identifier quoting and
``CREATE DATABASE``. No roles or servers are created; a role without
``CREATEDB`` fails cleanly.

Invokable from the installation venv:

    python -m y5n.runtime.store.event.backends.postgres.admin <dsn>

Exit 0 when the target database exists afterwards (created or already
there); prints ``created`` or ``exists`` to stdout; failures propagate as
a non-zero exit.
"""

from __future__ import annotations

import asyncio
import sys

from .dsn import admin_dsn, target_database


def quote_ident(name: str) -> str:
    """Quote a database identifier for ``CREATE DATABASE``.

    Always quoted, with embedded double quotes doubled — no injection and
    no dependence on ``search_path`` for the name.
    """
    if "\x00" in name:
        raise ValueError("invalid database identifier")
    return '"' + name.replace('"', '""') + '"'


async def ensure_database(dsn: str, *, maintenance_db: str = "postgres") -> None:
    """Ensure the target database exists; create it only when it does not.

    Connects through a maintenance database (default ``postgres``) with
    the same host/user/credentials as ``dsn``, checks ``pg_database`` and
    runs ``CREATE DATABASE`` when missing. Idempotent; errors (including
    missing ``CREATEDB``) propagate unchanged.
    """
    import asyncpg

    target = target_database(dsn)
    conn = await asyncpg.connect(admin_dsn(dsn, maintenance_db))
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", target
        )
        if exists:
            print("exists")
            return
        await conn.execute(f"CREATE DATABASE {quote_ident(target)}")
        print("created")
    finally:
        await conn.close()


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(
            "usage: python -m y5n.runtime.store.event.backends.postgres.admin <dsn>",
            file=sys.stderr,
        )
        return 2
    asyncio.run(ensure_database(args[0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
