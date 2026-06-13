from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from y5n.base.naming import Key, Namespace
from y5nstore.event.backends.memory import MemoryBackend
from y5nstore.event.batches.json_patch import JsonPatchStrategy
from y5nstore.event.models import (
    IndexKey,
    IndexSpec,
    IndexTerm,
    SnapshotHint,
    ValueType,
)
from y5nstore.event.store import ConcurrencyError, EntityStore

NS = Namespace("test", "widget")
PATCH = JsonPatchStrategy(max_ops=50)


def build_store() -> EntityStore:
    backend = MemoryBackend()
    return EntityStore(
        on_load_current=backend.load_current,
        on_load_current_many=backend.load_current_many,
        on_load_revisions=backend.load_revisions,
        on_load_snapshot=backend.load_snapshot_at_or_before,
        on_append_revision=backend.append_revision,
        on_upsert_current=backend.upsert_current,
        on_write_snapshot=backend.write_snapshot,
        on_index_ensure=backend.index_ensure,
        on_index_list=backend.index_list,
        on_index_replace_terms=backend.index_replace_terms,
        on_index_scan=backend.index_scan,
        on_gc=backend.gc,
        on_gc_global=backend.gc_global,
        writer=PATCH,
        readers={PATCH.format: PATCH},
    )


@pytest.fixture
def store() -> EntityStore:
    return build_store()


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
    assert r1.rev == 1
    r2 = await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 2}])
    assert r2.rev == 2
    r3 = await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 3}])
    assert r3.rev == 3

    loaded = await store.get(key=key)
    assert loaded.rev == 3


@pytest.mark.asyncio
async def test_get_returns_latest(store: EntityStore) -> None:
    key = NS.get_key("a")
    await store.append(key=key, patch=[{"op": "add", "path": "/name", "value": "alice"}])
    await store.append(key=key, patch=[{"op": "add", "path": "/name", "value": "bob"}])

    loaded = await store.get(key=key)
    assert loaded.data["name"] == "bob"


@pytest.mark.asyncio
async def test_as_of_returns_historical_state(store: EntityStore) -> None:
    key = NS.get_key("a")
    t0 = datetime.now(UTC)

    await store.append(key=key, patch=[
        {"op": "add", "path": "/name", "value": "alice"},
    ])
    t1 = datetime.now(UTC)

    await store.append(key=key, patch=[
        {"op": "add", "path": "/name", "value": "bob"},
    ])
    t2 = datetime.now(UTC)

    loaded = await store.get(key=key, at_time=t2)
    assert loaded.data["name"] == "bob"

    loaded = await store.get(key=key, at_time=t1)
    assert loaded.data["name"] == "alice"

    loaded = await store.get(key=key, at_time=t0)
    assert loaded is not None
    assert loaded.data is None or loaded.rev is None


@pytest.mark.asyncio
async def test_revisions_remain_ordered(store: EntityStore) -> None:
    key = NS.get_key("a")
    timestamps: list[datetime] = []
    for i in range(1, 6):
        r = await store.append(
            key=key,
            patch=[{"op": "add", "path": "/x", "value": i}],
        )
        timestamps.append(r.updated_at)

    for i, ts in enumerate(timestamps, start=1):
        loaded = await store.get(key=key, at_time=ts)
        assert loaded.rev == i, f"expected rev {i} at timestamp {i}"
        assert loaded.data == {"x": i}, f"expected data {{'x': {i}}} at timestamp {i}"


# ── expected_rev (Optimistic Concurrency) ──


@pytest.mark.asyncio
async def test_expected_rev_prevents_conflicts(store: EntityStore) -> None:
    key = NS.get_key("a")
    await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 1}])
    await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 2}])
    # rev is now 2, but we claim it's 1

    with pytest.raises(ConcurrencyError):
        await store.append(key=key, expected_rev=1,
                           patch=[{"op": "add", "path": "/x", "value": 3}])


@pytest.mark.asyncio
async def test_expected_rev_allows_correct_progress(store: EntityStore) -> None:
    key = NS.get_key("a")
    r1 = await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 1}])
    assert r1.rev == 1

    r2 = await store.append(key=key, expected_rev=1,
                             patch=[{"op": "add", "path": "/x", "value": 2}])
    assert r2.rev == 2


# ── replace & delete ──


@pytest.mark.asyncio
async def test_replace_overwrites(store: EntityStore) -> None:
    key = NS.get_key("a")
    await store.append(key=key, patch=[{"op": "add", "path": "/a", "value": 1}])
    await store.replace(key=key, doc={"b": 2})

    loaded = await store.get(key=key)
    assert loaded.data == {"b": 2}


@pytest.mark.asyncio
async def test_delete_sets_data_to_none(store: EntityStore) -> None:
    key = NS.get_key("a")
    await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 1}])
    await store.delete(key=key)

    loaded = await store.get(key=key)
    assert loaded.ok is False
    assert loaded.data is None


# ── Snapshots ──


@pytest.mark.asyncio
async def test_snapshots_dont_change_behavior(store: EntityStore) -> None:
    key = NS.get_key("a")
    expected = None
    for i in range(1, 101):
        await store.append(
            key=key,
            patch=[{"op": "add", "path": "/x", "value": i}],
            snapshot_hint=SnapshotHint.FORCE if i % 20 == 0 else SnapshotHint.AUTO,
        )
        expected = {"x": i}

    loaded = await store.get(key=key)
    assert loaded.data == expected
    assert loaded.rev == 100


@pytest.mark.asyncio
async def test_as_of_after_snapshots(store: EntityStore) -> None:
    key = NS.get_key("a")

    await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 10}])
    t_mid = datetime.now(UTC)

    for i in range(11, 101):
        await store.append(
            key=key,
            patch=[{"op": "add", "path": "/x", "value": i}],
            snapshot_hint=SnapshotHint.COMMIT if i % 30 == 0 else SnapshotHint.AUTO,
        )

    loaded = await store.get(key=key, at_time=t_mid)
    assert loaded.data == {"x": 10}


# ── Indexe ──


@pytest.mark.asyncio
async def test_scan_finds_indexed_entities(store: EntityStore) -> None:
    await store.ensure_indexes(
        namespace=NS,
        specs=[IndexSpec(key=IndexKey("email"), value_type=ValueType.TEXT)],
    )

    key = NS.get_key("a")
    await store.append(
        key=key,
        patch=[{"op": "add", "path": "/email", "value": "a@x"}],
        indexes=[IndexTerm(key=IndexKey("email"), value="a@x")],
    )

    keys, _ = await store.scan(namespace=NS, index_key=IndexKey("email"), value="a@x")
    assert keys == [key]


@pytest.mark.asyncio
async def test_scan_updates_after_replace(store: EntityStore) -> None:
    await store.ensure_indexes(
        namespace=NS,
        specs=[IndexSpec(key=IndexKey("email"), value_type=ValueType.TEXT)],
    )

    key = NS.get_key("a")
    await store.append(
        key=key,
        patch=[{"op": "add", "path": "/email", "value": "a@x"}],
        indexes=[IndexTerm(key=IndexKey("email"), value="a@x")],
    )
    await store.replace(
        key=key,
        doc={"email": "b@y"},
        indexes=[IndexTerm(key=IndexKey("email"), value="b@y")],
    )

    old_keys, _ = await store.scan(namespace=NS, index_key=IndexKey("email"), value="a@x")
    assert old_keys == []

    new_keys, _ = await store.scan(namespace=NS, index_key=IndexKey("email"), value="b@y")
    assert new_keys == [key]


@pytest.mark.asyncio
async def test_scan_removes_after_delete(store: EntityStore) -> None:
    await store.ensure_indexes(
        namespace=NS,
        specs=[IndexSpec(key=IndexKey("email"), value_type=ValueType.TEXT)],
    )

    key = NS.get_key("a")
    await store.append(
        key=key,
        patch=[{"op": "add", "path": "/email", "value": "a@x"}],
        indexes=[IndexTerm(key=IndexKey("email"), value="a@x")],
    )
    await store.delete(key=key)

    keys, _ = await store.scan(namespace=NS, index_key=IndexKey("email"), value="a@x")
    assert keys == []
