"""EventStoreFactory.provision — the schema of the configured backend.

``provision()`` shares the config language of ``build()``: ``memory`` is a
no-op, ``postgres`` applies the bundled schema (event store tables, index
and the sequencer's ``id_shards``). The postgres path is exercised with a
stub ``asyncpg`` — no PostgreSQL server and no new infrastructure in this
cut.
"""

from __future__ import annotations

import importlib.resources
import sys

import pytest

SCHEMA_PACKAGE = "y5n.runtime.store.sql.postgres"
SCHEMA_SCRIPTS = (
    "CREATE_STORE_TABLES.sql",
    "CREATE_STORE_INDEXES.sql",
    "CREATE_SEQUENCE_TABLES.sql",
)


class _FakeTransaction:
    def __init__(self, conn: _FakeConnection) -> None:
        self._conn = conn
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        self._conn._active_txn = self
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._conn._active_txn = None
        if exc_type is None:
            self.committed = True
        else:
            self.rolled_back = True
        self._conn.transactions.append(self)
        return False  # asyncpg propagates the error


class _FakeConnection:
    def __init__(self) -> None:
        self.executed: list[tuple[str, _FakeTransaction | None]] = []
        self.transactions: list[_FakeTransaction] = []
        self._active_txn: _FakeTransaction | None = None
        self.closed = False
        self.fail_on: int | None = None
        self.fail_error: Exception = RuntimeError("execute failed")

    async def execute(self, script: str) -> str:
        self.executed.append((script, self._active_txn))
        if self.fail_on is not None and len(self.executed) == self.fail_on:
            raise self.fail_error
        return "OK"

    def transaction(self) -> _FakeTransaction:
        return _FakeTransaction(self)

    async def close(self) -> None:
        self.closed = True


class _FakeAsyncPG:
    def __init__(self) -> None:
        self.connections: list[_FakeConnection] = []
        self.dsns: list[str] = []
        self.fail_on: int | None = None
        self.fail_error: Exception = RuntimeError("execute failed")

    async def connect(self, dsn: str):
        self.dsns.append(dsn)
        conn = _FakeConnection()
        conn.fail_on = self.fail_on
        conn.fail_error = self.fail_error
        self.connections.append(conn)
        return conn


@pytest.fixture
def fake_asyncpg(monkeypatch):
    fake = _FakeAsyncPG()
    monkeypatch.setitem(sys.modules, "asyncpg", fake)
    return fake


def _factory():
    from y5n.runtime.store.event.wire import EventStoreFactory

    return EventStoreFactory()


async def test_memory_provision_is_a_noop(fake_asyncpg):
    factory = _factory()

    assert await factory.provision(None) is None
    assert await factory.provision({"backend": "memory"}) is None

    assert fake_asyncpg.connections == []


async def test_provision_validates_config_like_build():
    factory = _factory()

    # postgres without a dsn is invalid for build() too.
    with pytest.raises(RuntimeError):
        await factory.provision({"backend": "postgres"})

    # Unknown backends are rejected the same way build() rejects them.
    with pytest.raises(RuntimeError):
        await factory.provision({"backend": "redis"})


async def test_provision_resolves_env_dsn_like_build(fake_asyncpg, monkeypatch):
    monkeypatch.setenv("IDENT_DATABASE", "postgresql://server/db")
    factory = _factory()

    await factory.provision({"backend": "postgres", "dsn": "env://IDENT_DATABASE"})

    assert fake_asyncpg.dsns == ["postgresql://server/db"]


async def test_provision_missing_env_dsn_raises_like_build():
    factory = _factory()

    with pytest.raises(RuntimeError, match="IDENT_DATABASE_UNSET"):
        await factory.provision(
            {"backend": "postgres", "dsn": "env://IDENT_DATABASE_UNSET"}
        )


async def test_postgres_provision_applies_all_schema_scripts(fake_asyncpg):
    factory = _factory()

    await factory.provision({"backend": "postgres", "dsn": "postgresql://server/db"})

    assert len(fake_asyncpg.connections) == 1
    conn = fake_asyncpg.connections[0]
    expected = [
        importlib.resources.files(SCHEMA_PACKAGE)
        .joinpath(name)
        .read_text(encoding="utf-8")
        for name in SCHEMA_SCRIPTS
    ]
    assert [script for script, _ in conn.executed] == expected


async def test_postgres_provision_is_atomic_in_one_transaction(fake_asyncpg):
    """The whole schema (all three scripts) lands in exactly one transaction."""
    factory = _factory()

    await factory.provision({"backend": "postgres", "dsn": "postgresql://server/db"})

    conn = fake_asyncpg.connections[0]
    assert len(conn.transactions) == 1
    txn = conn.transactions[0]
    assert txn.committed
    assert not txn.rolled_back
    # The full schema is three scripts, each executed inside that transaction.
    assert len(conn.executed) == 3
    for _, active in conn.executed:
        assert active is txn


async def test_postgres_provision_error_rolls_back_and_closes(fake_asyncpg):
    """An execute() failure propagates, rolls back and still closes."""
    factory = _factory()
    fake_asyncpg.fail_on = 2
    fake_asyncpg.fail_error = RuntimeError("boom at second script")

    with pytest.raises(RuntimeError, match="boom at second script"):
        await factory.provision(
            {"backend": "postgres", "dsn": "postgresql://server/db"}
        )

    conn = fake_asyncpg.connections[0]
    # The transaction went through the error path (rolled back), not commit.
    assert len(conn.transactions) == 1
    txn = conn.transactions[0]
    assert txn.rolled_back
    assert not txn.committed
    # Nothing after the failing statement was executed.
    assert len(conn.executed) == fake_asyncpg.fail_on
    # The connection is closed even though provisioning failed.
    assert conn.closed
