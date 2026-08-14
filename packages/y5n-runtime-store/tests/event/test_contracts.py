from __future__ import annotations

from datetime import UTC, datetime

import pytest
from y5n.runtime.api.naming import Namespace
from y5n.runtime.store.event.batches.json_patch import JsonPatchStrategy
from y5n.runtime.store.event.models import (
    IndexKey,
    IndexQueryTerm,
    IndexSpec,
    IndexTerm,
    SnapshotHint,
    ValueType,
)
from y5n.runtime.store.event.store import ConcurrencyError, EntityStore

NS = Namespace("test", "widget")
PATCH = JsonPatchStrategy(max_ops=50)


# ── append & Revisionen ──


@pytest.mark.asyncio
async def test_append_creates_revision(store: EntityStore) -> None:
    key = NS.get_key("a")
    result = await store.append(
        key=key, patch=[{"op": "add", "path": "/x", "value": 1}]
    )
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


# ── concurrency ──


@pytest.mark.asyncio
async def test_append_with_stale_expected_rev_raises(store: EntityStore) -> None:
    key = NS.get_key("a")
    r1 = await store.replace(key=key, doc={"x": 1})

    with pytest.raises(ConcurrencyError):
        await store.append(
            key=key,
            patch=[{"op": "add", "path": "/x", "value": 2}],
            expected_rev=0,
        )

    assert (await store.get(key=key)).rev == r1.rev


@pytest.mark.asyncio
async def test_append_with_matching_expected_rev_succeeds(store: EntityStore) -> None:
    key = NS.get_key("a")
    r1 = await store.replace(key=key, doc={"x": 1})

    r2 = await store.append(
        key=key,
        patch=[{"op": "add", "path": "/x", "value": 2}],
        expected_rev=r1.rev,
    )

    assert r2.rev == r1.rev + 1
    assert (await store.get(key=key)).data == {"x": 2}


# ── get_many ──


@pytest.mark.asyncio
async def test_get_many_mixed_hits_and_misses(store: EntityStore) -> None:
    await store.replace(key=NS.get_key("a"), doc={"name": "A"})
    await store.replace(key=NS.get_key("b"), doc={"name": "B"})

    results = await store.get_many(
        keys=[NS.get_key("a"), NS.get_key("missing"), NS.get_key("b")]
    )

    by_id = {r.key.id: r for r in results}
    assert by_id["a"].data == {"name": "A"}
    assert by_id["b"].data == {"name": "B"}
    assert by_id["missing"].data is None
    assert by_id["missing"].rev is None


@pytest.mark.asyncio
async def test_get_many_empty_returns_empty(store: EntityStore) -> None:
    assert await store.get_many(keys=[]) == []


# ── historical via snapshot + replay ──


@pytest.mark.asyncio
async def test_historical_get_replays_after_snapshot(store: EntityStore) -> None:
    key = NS.get_key("a")
    await store.append(
        key=key,
        patch=[{"op": "add", "path": "/x", "value": 1}],
        snapshot_hint=SnapshotHint.COMMIT,
    )
    ts1 = (await store.get(key=key)).as_of
    await store.append(key=key, patch=[{"op": "add", "path": "/x", "value": 2}])
    ts2 = (await store.get(key=key)).as_of

    loaded = await store.get(key=key, at_time=ts1)
    assert loaded.data == {"x": 1}
    assert loaded.historical is True

    loaded2 = await store.get(key=key, at_time=ts2)
    assert loaded2.data == {"x": 2}


# ── scan ──


@pytest.mark.asyncio
async def test_scan_eq_with_limit(store: EntityStore) -> None:
    await store.ensure_indexes(
        namespace=NS,
        specs=[IndexSpec(key=IndexKey("color"), value_type=ValueType.TEXT)],
    )
    for name, color in [("a", "red"), ("b", "blue"), ("c", "red"), ("d", "red")]:
        await store.replace(
            key=NS.get_key(name),
            doc={"name": name},
            indexes=[IndexTerm(key=IndexKey("color"), value=color)],
        )

    keys, cursor = await store.scan(
        namespace=NS,
        index_key=IndexKey("color"),
        value="red",
        limit=2,
    )
    assert len(keys) == 2
    assert cursor is not None

    # next page via cursor (only one "red" entity remains)
    keys2, cursor2 = await store.scan(
        namespace=NS,
        index_key=IndexKey("color"),
        value="red",
        limit=2,
        cursor=cursor,
    )
    assert len(keys2) == 1
    assert {k.id for k in keys} != {k.id for k in keys2}

    # exhausted after the final page
    keys3, cursor3 = await store.scan(
        namespace=NS,
        index_key=IndexKey("color"),
        value="red",
        limit=2,
        cursor=cursor2,
    )
    assert keys3 == []
    assert cursor3 is None


@pytest.mark.asyncio
async def test_scan_range(store: EntityStore) -> None:
    await store.ensure_indexes(
        namespace=NS,
        specs=[IndexSpec(key=IndexKey("num"), value_type=ValueType.INT)],
    )
    for n in range(5):
        await store.replace(
            key=NS.get_key(f"k{n}"),
            doc={"n": n},
            indexes=[IndexTerm(key=IndexKey("num"), value=n)],
        )

    keys, _ = await store.scan(
        namespace=NS,
        index_key=IndexKey("num"),
        lo=1,
        hi=3,
    )
    assert sorted(int(k.id[-1]) for k in keys) == [1, 2, 3]


@pytest.mark.asyncio
async def test_scan_prefix(store: EntityStore) -> None:
    await store.ensure_indexes(
        namespace=NS,
        specs=[IndexSpec(key=IndexKey("tag"), value_type=ValueType.TEXT)],
    )
    for name in ["alpha", "alpine", "beta"]:
        await store.replace(
            key=NS.get_key(name),
            doc={"name": name},
            indexes=[IndexTerm(key=IndexKey("tag"), value=name)],
        )

    keys, _ = await store.scan(
        namespace=NS,
        index_key=IndexKey("tag"),
        prefix="alp",
    )
    assert sorted(k.id for k in keys) == ["alpha", "alpine"]


@pytest.mark.asyncio
async def test_scan_rejects_prefix_with_value(store: EntityStore) -> None:
    with pytest.raises(ValueError, match="prefix"):
        await store.scan(
            namespace=NS,
            index_key=IndexKey("tag"),
            value="x",
            prefix="alp",
        )


@pytest.mark.asyncio
async def test_scan_rejects_cursor_mismatch(store: EntityStore) -> None:
    await store.ensure_indexes(
        namespace=NS,
        specs=[IndexSpec(key=IndexKey("color"), value_type=ValueType.TEXT)],
    )
    await store.replace(
        key=NS.get_key("a"),
        doc={"name": "a"},
        indexes=[IndexTerm(key=IndexKey("color"), value="red")],
    )

    keys, cursor = await store.scan(
        namespace=NS, index_key=IndexKey("color"), value="red"
    )
    assert cursor is not None

    with pytest.raises(ValueError, match="cursor mismatch"):
        await store.scan(
            namespace=NS,
            index_key=IndexKey("other"),
            value="x",
            cursor=cursor,
        )
