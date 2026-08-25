"""Packaging decisions of y5n-runtime-store.

``asyncpg`` is a normal (non-optional) dependency: Yakoon installs a
complete runtime whose EventStoreFactory offers postgres out of the box —
without a second dependency lifecycle (a ``postgres`` extra that the
installer has to activate). The postgres backend stays lazily imported;
packaging and import-time behavior are separate questions.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _pyproject() -> dict:
    with open(PYPROJECT, "rb") as f:
        return tomllib.load(f)


def test_asyncpg_is_a_normal_dependency():
    data = _pyproject()
    deps = data["project"].get("dependencies") or []
    assert "asyncpg" in deps


def test_asyncpg_is_not_hidden_in_a_postgres_extra():
    data = _pyproject()
    optional = data["project"].get("optional-dependencies") or {}
    assert "postgres" not in optional
