"""PostgreSQL schema resources are package resources of the runtime store.

The postgres backend ships with its DDL as package resources, readable
from a wheel through ``importlib.resources`` — the schema belongs to the
EventStore component, not to a manual setup script. ``EMPTY.sql`` is a
destructive maintenance script, not a schema resource, and must never
appear here.
"""

from __future__ import annotations

import importlib.resources

SCHEMA_PACKAGE = "y5n.runtime.store.sql.postgres"
SCHEMA_FILES = {
    "CREATE_TABLE.sql",
    "CREATE_INDEX.sql",
    "id_shards.sql",
}


def _schema() -> importlib.resources.abc.Traversable:
    return importlib.resources.files(SCHEMA_PACKAGE)


def test_schema_package_exposes_exactly_the_schema_files():
    names = {r.name for r in _schema().iterdir()}

    assert SCHEMA_FILES <= names
    # The destructive maintenance script is not a schema resource.
    assert "EMPTY.sql" not in names


def test_every_schema_file_is_non_empty():
    for name in SCHEMA_FILES:
        data = _schema().joinpath(name).read_text(encoding="utf-8")
        assert data.strip(), f"{name} is empty"


def test_schema_files_carry_the_expected_ddl():
    tables = _schema().joinpath("CREATE_TABLE.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS current" in tables
    assert "CREATE TABLE IF NOT EXISTS revisions" in tables
    assert "CREATE TABLE IF NOT EXISTS id_shards" not in tables

    index = _schema().joinpath("CREATE_INDEX.sql").read_text(encoding="utf-8")
    assert "CREATE INDEX IF NOT EXISTS idx_index_lookup" in index

    shards = _schema().joinpath("id_shards.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS id_shards" in shards
