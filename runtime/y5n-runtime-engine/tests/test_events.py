"""Phase 3 — events list/show (ADR-17): audit as a saved view.

The events commands read the runtime's history from the shared Event
Store. These tests wire a store on the bus, record events, then drive the
events.main() command logic with a captured io.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest
from y5n.runtime.api.runtime.bus import _make_default_bus, get_bus, set_bus
from y5n.runtime.engine.services.activity import ActivityService, activity_namespace
from y5n.runtime.engine.wire.adapter.store import StoreAdapter
from y5n.runtime.store.event.backends.memory import MemoryBackend
from y5n.runtime.store.event.store import create_entity_store
from y5n.runtime.store.sequence.allocator import ShardAllocator
from y5n.runtime.store.sequence.backends.memory import MemoryShardRepository
from y5n.runtime.store.sequence.runtime import Sequencer


@pytest.fixture
def bus_store(monkeypatch):
    import os

    os.environ.setdefault("YAK_ENDPOINT", "inprocess://")

    previous = get_bus()
    bus = _make_default_bus()
    set_bus(bus)

    store = create_entity_store(MemoryBackend())
    sequencer = Sequencer(ShardAllocator(MemoryShardRepository()))
    bus.transport.register_adapter("store", StoreAdapter(store, sequencer))
    bus.resolver.register(
        "system:store",
        {
            "store": [
                "get",
                "get_many",
                "append",
                "replace",
                "record",
                "delete",
                "scan",
                "history",
                "ensure_indexes",
                "query_index",
                "next_id",
            ]
        },
        path="/",
    )

    activity = ActivityService(
        on_record=store.record,
        on_ensure_indexes=store.ensure_indexes,
    )
    yield activity
    set_bus(previous)


async def _record(activity: ActivityService, kind: str) -> None:
    from y5n.runtime.api.naming import Key

    class _Session:
        key = Key.from_parts("test", "session", "runtime", "s-1")

        def get_identity(self):
            return Key.from_parts("users", "user", "global", "u-1")

        @property
        def user_name(self):
            return "stefan"

        @property
        def security_context(self):
            return "normal"

    await activity.ensure_index()
    await activity.record(kind=kind, session=_Session(), payload={"path": "/opt"})


def _capture_io(monkeypatch):
    from y5n.sdk import io as sdk_io

    lines: list[str] = []

    async def write(view, *, mode=None, **kwargs):
        lines.append(view if isinstance(view, str) else str(view))

    monkeypatch.setattr(sdk_io, "write", write)
    return lines


@pytest.mark.asyncio
async def test_events_list_shows_recorded_events(bus_store, monkeypatch):
    await _record(bus_store, "command.executed")
    await _record(bus_store, "permission.denied")

    lines = _capture_io(monkeypatch)

    from y5n.packs.system.events import list as events_list

    await events_list.main()

    text = "\n".join(lines)
    assert "command.executed" in text
    assert "permission.denied" in text
    assert "Events:" in text


@pytest.mark.asyncio
async def test_events_show_displays_context(bus_store, monkeypatch):
    from y5n.runtime.api.naming import Key
    from y5n.sdk import io as sdk_io

    await bus_store.ensure_index()
    session = _FakeSession()
    await bus_store.record(kind="command.executed", session=session)

    # Find the written event id.
    from y5n.runtime.api.runtime.bus import get_bus

    store_adapter = None
    for adapter in get_bus().transport._adapters.values():
        if isinstance(adapter, StoreAdapter):
            store_adapter = adapter
            break

    page = await store_adapter.scan(
        None, namespace="system/activity/global", index_key="all", value="1"
    )
    event_key = page["keys"][0]
    event_id = event_key.rsplit("#", 1)[-1]

    lines: list[str] = []

    async def write(view, *, mode=None, **kwargs):
        lines.append(view if isinstance(view, str) else str(view))

    monkeypatch.setattr(sdk_io, "write", write)

    import y5n.packs.system.events.show as show_mod

    monkeypatch.setattr(show_mod, "context", _FakeContextModule(event_id))

    await show_mod.main()

    text = "\n".join(lines)
    assert f"Event {event_id}" in text
    assert "command.executed" in text
    assert "stefan" in text


class _FakeSession:
    @property
    def key(self):
        from y5n.runtime.api.naming import Key

        return Key.from_parts("test", "session", "runtime", "s-1")

    def get_identity(self):
        from y5n.runtime.api.naming import Key

        return Key.from_parts("users", "user", "global", "u-1")

    @property
    def user_name(self):
        return "stefan"

    @property
    def security_context(self):
        return "normal"


class _FakeContextModule:
    def __init__(self, event_id):
        self._event_id = event_id

    def current(self):
        return _FakeContextInstance(self._event_id)


class _FakeContextInstance:
    def __init__(self, event_id):
        self.args = [event_id]
