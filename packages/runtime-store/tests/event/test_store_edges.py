"""EntityStore edge-case unit tests.

Covers store paths that the memory-backend contract tests cannot reach:
  - historical get with no snapshot present
  - replay with an unknown patch format (missing reader)
  - scan with a timezone-naive cursor as-of
  - scan rejecting prefix + range
  - age-based automatic snapshot
  - prefix_end boundaries
  - encode/decode cursor round trip and malformed input
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from y5n.runtime.api.naming import Namespace
from y5n.runtime.store.event.batches.json_patch import JsonPatchStrategy
from y5n.runtime.store.event.models import (
    CurrentRow,
    EntityId,
    IndexKey,
    PatchFormat,
    RevisionRow,
    ScanCursor,
    SnapshotHint,
    SnapshotRow,
)
from y5n.runtime.store.event.models.mode import ScanMode
from y5n.runtime.store.event.store import (
    EntityStore,
    decode_cursor,
    encode_cursor,
    prefix_end,
)

NS = Namespace("test", "widget")
PATCH = JsonPatchStrategy(max_ops=50)


def _make_store(**overrides) -> EntityStore:
    calls = {
        "load_current": AsyncMock(return_value=None),
        "load_current_many": AsyncMock(return_value={}),
        "load_revisions": AsyncMock(return_value=[]),
        "load_snapshot": AsyncMock(return_value=None),
        "append_revision": AsyncMock(),
        "upsert_current": AsyncMock(),
        "write_snapshot": AsyncMock(),
        "index_ensure": AsyncMock(),
        "index_list": AsyncMock(return_value=[]),
        "index_replace_terms": AsyncMock(),
        "index_scan": AsyncMock(return_value=[]),
        "query_index": AsyncMock(return_value=[]),
    }
    calls.update(overrides)
    return EntityStore(
        on_load_current=calls["load_current"],
        on_load_current_many=calls["load_current_many"],
        on_load_revisions=calls["load_revisions"],
        on_load_snapshot=calls["load_snapshot"],
        on_append_revision=calls["append_revision"],
        on_upsert_current=calls["upsert_current"],
        on_write_snapshot=calls["write_snapshot"],
        on_index_ensure=calls["index_ensure"],
        on_index_list=calls["index_list"],
        on_index_replace_terms=calls["index_replace_terms"],
        on_index_scan=calls["index_scan"],
        on_query_index=calls["query_index"],
        writer=PATCH,
        readers={PATCH.format: PATCH},
    )


# ── historical get without snapshot ──


@pytest.mark.asyncio
async def test_historical_get_without_snapshot_replays_from_scratch() -> None:
    ts = datetime.now(UTC)
    store = _make_store(
        load_revisions=AsyncMock(
            return_value=[
                RevisionRow(
                    entity_id=EntityId("a"),
                    rev=1,
                    ts=ts,
                    patch=[{"op": "add", "path": "/x", "value": 1}],
                    patch_format=PatchFormat.JSONPATCH,
                )
            ]
        )
    )

    loaded = await store.get(key=NS.get_key("a"), at_time=ts)

    assert loaded.data == {"x": 1}
    assert loaded.historical is True
    assert loaded.rev == 1


# ── replay with unknown patch format ──


@pytest.mark.asyncio
async def test_historical_get_unknown_format_raises() -> None:
    ts = datetime.now(UTC)
    store = _make_store(
        load_snapshot=AsyncMock(
            return_value=SnapshotRow(
                entity_id=EntityId("a"), rev=0, ts=ts - timedelta(1), data={}
            )
        ),
        load_revisions=AsyncMock(
            return_value=[
                RevisionRow(
                    entity_id=EntityId("a"),
                    rev=1,
                    ts=ts,
                    patch=[{"op": "add", "path": "/x", "value": 1}],
                    patch_format=PatchFormat.FASTPATCH,
                )
            ]
        ),
    )

    with pytest.raises(RuntimeError, match="No patch reader"):
        await store.get(key=NS.get_key("a"), at_time=ts)


# ── cursor as-of must be timezone-aware ──


@pytest.mark.asyncio
async def test_scan_rejects_naive_cursor_asof() -> None:
    store = _make_store()
    cursor = encode_cursor(
        ScanCursor(
            index_key="k",
            mode=ScanMode.EQ,
            value="v",
            entity_id="a",
            asof="2026-01-01T00:00:00",  # naive ISO
        )
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        await store.scan(
            namespace=NS,
            index_key=IndexKey("k"),
            value="v",
            cursor=cursor,
        )


@pytest.mark.asyncio
async def test_scan_rejects_prefix_with_range() -> None:
    store = _make_store()

    with pytest.raises(ValueError, match="prefix"):
        await store.scan(
            namespace=NS,
            index_key=IndexKey("k"),
            prefix="pre",
            lo="a",
        )


# ── age-based automatic snapshot ──


@pytest.mark.asyncio
async def test_age_based_snapshot_written_when_old() -> None:
    now = datetime.now(UTC)
    old = now - timedelta(seconds=60)
    store = _make_store(
        load_current=AsyncMock(
            return_value=CurrentRow(
                entity_id=EntityId("a"),
                rev=1,
                data={"x": 1},
                updated_at=now,
            )
        ),
        load_snapshot=AsyncMock(
            return_value=SnapshotRow(
                entity_id=EntityId("a"), rev=1, ts=old, data={"x": 1}
            )
        ),
    )
    store._snap = store._snap.__class__(max_age_seconds=15)

    result = await store.append(
        key=NS.get_key("a"),
        patch=[{"op": "add", "path": "/x", "value": 2}],
    )

    assert result.snapshot_written is True


@pytest.mark.asyncio
async def test_revision_count_snapshot_written() -> None:
    now = datetime.now(UTC)
    store = _make_store(
        load_current=AsyncMock(
            return_value=CurrentRow(
                entity_id=EntityId("a"),
                rev=19,
                data={"x": 1},
                updated_at=now,
            )
        ),
        load_snapshot=AsyncMock(
            return_value=SnapshotRow(entity_id=EntityId("a"), rev=0, ts=now, data={})
        ),
    )
    store._snap = store._snap.__class__(every_n_revisions=20)

    result = await store.append(
        key=NS.get_key("a"),
        patch=[{"op": "add", "path": "/x", "value": 2}],
        snapshot_hint=SnapshotHint.NONE,
    )

    assert result.snapshot_written is True


@pytest.mark.asyncio
async def test_recent_snapshot_not_written() -> None:
    now = datetime.now(UTC)
    recent = now - timedelta(seconds=1)
    store = _make_store(
        load_current=AsyncMock(
            return_value=CurrentRow(
                entity_id=EntityId("a"),
                rev=1,
                data={"x": 1},
                updated_at=now,
            )
        ),
        load_snapshot=AsyncMock(
            return_value=SnapshotRow(
                entity_id=EntityId("a"), rev=1, ts=recent, data={"x": 1}
            )
        ),
    )
    store._snap = store._snap.__class__(max_age_seconds=15)

    result = await store.append(
        key=NS.get_key("a"),
        patch=[{"op": "add", "path": "/x", "value": 2}],
        snapshot_hint=SnapshotHint.NONE,
    )

    assert result.snapshot_written is False


# ── prefix_end boundaries ──


def test_prefix_end_empty_returns_none() -> None:
    assert prefix_end("") is None


def test_prefix_end_increments_last_char() -> None:
    assert prefix_end("alp") == "alq"


def test_prefix_end_max_code_point_returns_none() -> None:
    assert prefix_end("\U0010ffff") is None


# ── cursor encode/decode round trip ──


def test_cursor_round_trip() -> None:
    cursor = ScanCursor(
        index_key="color",
        mode=ScanMode.EQ,
        value="red",
        entity_id="a",
        asof=datetime.now(UTC).isoformat(),
    )

    encoded = encode_cursor(cursor)
    decoded = decode_cursor(encoded)

    assert decoded.index_key == cursor.index_key
    assert decoded.mode == cursor.mode
    assert decoded.value == cursor.value
    assert decoded.entity_id == cursor.entity_id
    assert decoded.asof == cursor.asof


def test_decode_cursor_missing_asof_raises() -> None:
    import base64
    import json

    raw = json.dumps({"ik": "k", "m": "eq", "v": "x", "id": "a"}).encode()
    encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

    with pytest.raises(ValueError, match="asof"):
        decode_cursor(encoded)
