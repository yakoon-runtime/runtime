"""PostgreSQL database administration of the runtime store.

``ensure_database`` is infrastructure, separate from schema provisioning:
it ensures the target database exists (maintenance connection, idempotent,
quoted ``CREATE DATABASE``). ``provision`` surfaces a missing target
database as the stable ``DatabaseDoesNotExist`` instead of a raw asyncpg
error. All via a stub ``asyncpg`` — no PostgreSQL server needed.
"""

from __future__ import annotations

import sys
import types

import pytest

DSN = "postgresql://postgres:secret@localhost:5432/yakoon_ident"


# ---------------------------------------------------------------
# DSN helpers
# ---------------------------------------------------------------


def test_parse_and_target_database():
    from y5n.runtime.store.event.backends.postgres.dsn import (
        parse_dsn,
        target_database,
    )

    parsed = parse_dsn(DSN)
    assert parsed.user == "postgres"
    assert parsed.password == "secret"
    assert parsed.host == "localhost"
    assert parsed.port == 5432
    assert parsed.database == "yakoon_ident"
    assert target_database(DSN) == "yakoon_ident"


def test_target_database_without_name_raises():
    from y5n.runtime.store.event.backends.postgres.dsn import target_database

    with pytest.raises(ValueError):
        target_database("postgresql://postgres:secret@localhost:5432/")


def test_admin_dsn_same_connection_other_database():
    from y5n.runtime.store.event.backends.postgres.dsn import admin_dsn

    admin = admin_dsn(DSN)
    assert admin == "postgresql://postgres:secret@localhost:5432/postgres"

    custom = admin_dsn(DSN, maintenance_db="template1")
    assert custom == "postgresql://postgres:secret@localhost:5432/template1"


def test_admin_dsn_preserves_query_params():
    from y5n.runtime.store.event.backends.postgres.dsn import admin_dsn

    dsn = "postgresql://u:p@h:5/db?sslmode=disable"
    assert admin_dsn(dsn) == "postgresql://u:p@h:5/postgres?sslmode=disable"


# ---------------------------------------------------------------
# Identifier quoting
# ---------------------------------------------------------------


def test_quote_ident_always_quotes_and_doubles_embedded_quotes():
    from y5n.runtime.store.event.backends.postgres.admin import quote_ident

    assert quote_ident("yakoon_ident") == '"yakoon_ident"'
    assert quote_ident('weird"name') == '"weird""name"'
    with pytest.raises(ValueError):
        quote_ident("bad\x00name")


# ---------------------------------------------------------------
# ensure_database via a stub asyncpg
# ---------------------------------------------------------------


class _FakeConnection:
    def __init__(self, exists_result=None, fail_execute=None) -> None:
        self.exists_result = exists_result
        self.fail_execute = fail_execute
        self.executed: list[str] = []
        self.existence_checks: list[tuple[str, str]] = []
        self.closed = False

    async def fetchval(self, query: str, *args):
        self.existence_checks.append((query, args[0]))
        return self.exists_result

    async def execute(self, sql: str):
        self.executed.append(sql)
        if self.fail_execute is not None:
            raise self.fail_execute

    async def close(self) -> None:
        self.closed = True


class InvalidCatalogNameError(Exception):
    pass


class _FakeAsyncPG:
    def __init__(self, conn=None, connect_error=None) -> None:
        self._conn = conn
        self._connect_error = connect_error
        self.dsns: list[str] = []
        self.connections: list[_FakeConnection] = []

    async def connect(self, dsn: str):
        self.dsns.append(dsn)
        if self._connect_error is not None:
            raise self._connect_error
        self.connections.append(self._conn)
        return self._conn

    @property
    def invalid_catalog_name_error(self):
        return InvalidCatalogNameError


def _asyncpg_module(fake) -> types.SimpleNamespace:
    """The sys.modules stand-in for asyncpg (connect + exception class)."""
    return types.SimpleNamespace(
        connect=fake.connect,
        InvalidCatalogNameError=InvalidCatalogNameError,
    )


@pytest.fixture
def fake_asyncpg(monkeypatch):
    fake = _FakeAsyncPG(conn=_FakeConnection())
    monkeypatch.setitem(sys.modules, "asyncpg", _asyncpg_module(fake))
    return fake


async def test_ensure_database_connects_via_maintenance_database(fake_asyncpg):
    from y5n.runtime.store.event.backends.postgres.admin import ensure_database

    fake_asyncpg._conn.exists_result = None
    await ensure_database(DSN)

    assert fake_asyncpg.dsns == ["postgresql://postgres:secret@localhost:5432/postgres"]


async def test_ensure_database_creates_missing_database(fake_asyncpg, capsys):
    from y5n.runtime.store.event.backends.postgres.admin import ensure_database

    fake_asyncpg._conn.exists_result = None
    await ensure_database(DSN)

    assert fake_asyncpg._conn.executed == ['CREATE DATABASE "yakoon_ident"']
    assert capsys.readouterr().out.strip() == "created"


async def test_ensure_database_quotes_odd_identifier(fake_asyncpg):
    from y5n.runtime.store.event.backends.postgres.admin import ensure_database

    fake_asyncpg._conn.exists_result = None
    await ensure_database('postgresql://u:p@h/weird"db')

    assert fake_asyncpg._conn.executed == ['CREATE DATABASE "weird""db"']


async def test_ensure_database_is_idempotent_when_present(fake_asyncpg, capsys):
    from y5n.runtime.store.event.backends.postgres.admin import ensure_database

    fake_asyncpg._conn.exists_result = 1
    await ensure_database(DSN)

    assert fake_asyncpg._conn.executed == []
    assert capsys.readouterr().out.strip() == "exists"


async def test_ensure_database_propagates_errors(fake_asyncpg):
    from y5n.runtime.store.event.backends.postgres.admin import ensure_database

    boom = RuntimeError("permission denied to create database")
    fake_asyncpg._conn.exists_result = None
    fake_asyncpg._conn.fail_execute = boom

    with pytest.raises(RuntimeError, match="permission denied"):
        await ensure_database(DSN)
    assert fake_asyncpg._conn.closed


def test_main_entrypoint_runs_ensure_database(fake_asyncpg, capsys):
    from y5n.runtime.store.event.backends.postgres import admin

    fake_asyncpg._conn.exists_result = None
    assert admin.main([DSN]) == 0
    assert "created" in capsys.readouterr().out
    assert admin.main([DSN, "extra"]) == 2


# ---------------------------------------------------------------
# DatabaseDoesNotExist from provisioning
# ---------------------------------------------------------------


async def test_provision_surfaces_missing_database(monkeypatch):
    from y5n.runtime.store.event.backends.postgres import provision

    fake = _FakeAsyncPG(
        conn=_FakeConnection(),
        connect_error=InvalidCatalogNameError('database "yakoon_ident" does not exist'),
    )
    monkeypatch.setitem(sys.modules, "asyncpg", _asyncpg_module(fake))

    with pytest.raises(provision.DatabaseDoesNotExist) as excinfo:
        await provision.provision_postgres_schema(DSN)

    assert excinfo.value.database == "yakoon_ident"
    assert 'database "yakoon_ident" does not exist' in str(excinfo.value)
