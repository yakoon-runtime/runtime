from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from y5n.base.naming import Key, Namespace
from y5nstore.event.batches.json_patch import JsonPatchStrategy
from y5nstore.event.models import (
    IndexKey,
    IndexQueryTerm,
    IndexSpec,
    IndexTerm,
    SnapshotHint,
    ValueType,
)
from y5nstore.event.store import EntityStore

NS = Namespace("test", "widget")
PATCH = JsonPatchStrategy(max_ops=50)


# ── append & Revisionen ──


@pytest.mark.asyncio
async def test_append_creates_revision(store: EntityStore) -> None:
    key = NS.get_key("a")
    result = await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 1}])
    assert result.rev == 1

    loaded = await store.get(key=key)
    assert loaded.rev == 1
    assert loaded.data == {"x": 1}


@pytest.mark.asyncio
async def test_append_increments_revision(store: EntityStore) -> None:
    key = NS.get_key("a")
    r1 = await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 1}])
    r2 = await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 2}])
    assert r2.rev == r1.rev + 1


@pytest.mark.asyncio
async def test_get_returns_latest(store: EntityStore) -> None:
    key = NS.get_key("a")
    await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 1}])
    await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 2}])

    loaded = await store.get(key=key)
    assert loaded.data == {"x": 2}


@pytest.mark.asyncio
async def test_as_of_returns_historical_state(store: EntityStore) -> None:
    key = NS.get_key("a")
    await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 1}])
    ts = datetime.now(UTC)
    await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 2}])

    loaded = await store.get(key=key, at_time=ts)
    assert loaded.data == {"x": 1}


# ── replace ──


@pytest.mark.asyncio
async def test_replace_creates_or_overwrites(store: EntityStore) -> None:
    key = NS.get_key("a")
    result = await store.replace(key=key, doc={"name": "Alice"})
    assert result.rev == 1

    loaded = await store.get(key=key)
    assert loaded.data == {"name": "Alice"}

    result2 = await store.replace(key=key, doc={"name": "Bob"})
    assert result2.rev == result.rev + 1

    loaded = await store.get(key=key)
    assert loaded.data == {"name": "Bob"}


# ── query_index ──


@pytest.mark.asyncio
async def test_query_index_returns_matching_keys(store: EntityStore) -> None:
    await store.ensure_indexes(
        namespace=NS,
        specs=[IndexSpec(key=IndexKey("color"), value_type=ValueType.TEXT)],
    )

    for name, color in [("a", "red"), ("b", "blue"), ("c", "red")]:
        key = NS.get_key(name)
        await store.replace(
            key=key,
            doc={"name": name},
            indexes=[IndexTerm(key=IndexKey("color"), value=color)],
        )

    keys, _ = await store.query_index(
        namespace=NS,
        terms=[IndexQueryTerm(index_key=IndexKey("color"), op="eq", value="red")],
        mode="and",
    )
    assert len(keys) == 2


# ── snapshot_hint ──


@pytest.mark.asyncio
async def test_snapshot_hint_skips_intermediate(store: EntityStore) -> None:
    key = NS.get_key("a")
    for v in range(5):
        await store.append(
            key=key,
            patch=[{"op": "add", "path": "/x", "value": v}],
            snapshot_hint=SnapshotHint.NONE,
        )
    await store.append(
        key=key,
        patch=[{"op": "add", "path": "/x", "value": 5}],
        snapshot_hint=SnapshotHint.COMMIT,
    )
    loaded = await store.get(key=key)
    assert loaded.data == {"x": 5}


# ── delete ──


@pytest.mark.asyncio
async def test_delete_marks_as_removed(store: EntityStore) -> None:
    key = NS.get_key("a")
    await store.replace(key=key, doc={"name": "Alice"})
    loaded = await store.get(key=key)
    assert loaded.data is not None

    await store.delete(key=key)
    loaded = await store.get(key=key)
    assert loaded.data is None


# ── indexes ──


@pytest.mark.asyncio
async def test_index_lifecycle(store: EntityStore) -> None:
    spec = IndexSpec(key=IndexKey("tag"), value_type=ValueType.TEXT)

    # ensure
    await store.ensure_indexes(namespace=NS, specs=[spec])

    # list
    specs = await store.list_indexes(namespace=NS)
    assert len(specs) == 1
    assert specs[0].key == IndexKey("tag")
