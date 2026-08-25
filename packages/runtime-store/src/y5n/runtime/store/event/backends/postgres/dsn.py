"""Small PostgreSQL DSN helpers.

The postgres backend owns the DSN language (ADR-19: the factory owns its
config language). Parsing stays dependency-free so the same helpers serve
provisioning and the database-admin primitive.
"""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass


@dataclass(frozen=True)
class Dsn:
    user: str | None
    password: str | None
    host: str | None
    port: int | None
    database: str | None
    query: tuple[tuple[str, str], ...]


def parse_dsn(dsn: str) -> Dsn:
    parts = urllib.parse.urlsplit(dsn)
    database = parts.path.lstrip("/") or None
    return Dsn(
        user=parts.username,
        password=parts.password,
        host=parts.hostname,
        port=parts.port,
        database=database,
        query=tuple(urllib.parse.parse_qsl(parts.query)),
    )


def target_database(dsn: str) -> str:
    """The database name the DSN addresses — the admin target."""
    database = parse_dsn(dsn).database
    if not database:
        raise ValueError("DSN carries no database name")
    return database


def admin_dsn(dsn: str, maintenance_db: str = "postgres") -> str:
    """The same connection, but pointing at an existing maintenance database.

    Host, user, credentials and query params are preserved verbatim; only
    the path (the database) is replaced.
    """
    parts = urllib.parse.urlsplit(dsn)
    return urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, f"/{maintenance_db}", parts.query, "")
    )
