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
def bus_store(tmp_path, monkeypatch):
    import os

    os.environ.setdefault("YAK_ENDPOINT", "inprocess://")

    from y5n.runtime.api.runtime.context import set_context
    from y5n.runtime.engine.executor import (
        ExecutorKind,
        ExecutorRegistry,
        RuntimeExecutor,
    )
    from y5n.runtime.engine.nodes.tree import Tree
    from y5n.runtime.engine.wire.adapter.store import StoreResolver
    from y5n.runtime.store.event.runtime import StoreRuntime

    # The events commands declare the `runtime` store and read activity
    # directly (ADR-19: strict resolution, no default store).
    (tmp_path / "usr" / "bin" / "events" / ".yak").mkdir(parents=True, exist_ok=True)
    (tmp_path / "usr" / "bin" / "events" / ".yak" / "yak.yml").write_text(
        "stores:\n  - runtime\n"
    )
    executors = ExecutorRegistry()
    executors.register(ExecutorKind.RUNTIME, RuntimeExecutor())
    tree = Tree(root_path=tmp_path, executors=executors)
    tree.build()

    previous = get_bus()
    bus = _make_default_bus()
    set_bus(bus)

    store = create_entity_store(MemoryBackend())
    runtime = StoreRuntime(
        objects=store,
        sequencer=Sequencer(ShardAllocator(MemoryShardRepository())),
    )
    bus.transport.register_adapter(
        "store",
        StoreAdapter(
            resolver=StoreResolver(tree=tree, stores={"runtime": runtime}),
        ),
    )
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
    set_context({"node": {"path": "/usr/bin/events", "stores": ["runtime"]}})
    try:
        yield activity
    finally:
        set_context({})
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

    import y5n.packs.system.events.list as list_mod
    from y5n.packs.system.events import list as events_list

    monkeypatch.setattr(list_mod, "context", _FakeContextModule(""))

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

    from y5n.runtime.api.runtime.invoke import Call

    call = Call(
        port="store",
        method="",
        caller_path="/usr/bin/events",
        caller_session_key="test/session/runtime#s-1",
    )
    page = await store_adapter.scan(
        call, namespace="system/activity/global", index_key="all", value="1"
    )
    event_key = page["keys"][0]
    event_id = event_key["id"]

    lines: list[str] = []

    async def write(view, *, mode=None, **kwargs):
        lines.append(view if isinstance(view, str) else str(view))

    monkeypatch.setattr(sdk_io, "write", write)

    import y5n.packs.system.events.show as show_mod

    monkeypatch.setattr(show_mod, "context", _FakeContextModule(event_id))

    await show_mod.main()

    text = "\n".join(lines)
    assert f"Event {event_id[:8]}" in text
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

    def request(self):
        return _FakeRequest([self._event_id])

    def current(self):
        return _FakeContextInstance(self._event_id)


class _FakeRequest:
    def __init__(self, tokens):
        self._tokens = tokens

    def has_args(self):
        return bool(self._tokens)

    def arg(self, index, default=None):
        return self._tokens[index] if index < len(self._tokens) else default

    def option(self, name, default=None):
        return default


class _FakeContextInstance:
    def __init__(self, event_id):
        self.args = [event_id]
