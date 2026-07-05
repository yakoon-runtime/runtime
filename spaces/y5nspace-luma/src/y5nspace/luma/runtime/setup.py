from __future__ import annotations

from y5n.api.nodes import NodeSpace
from y5nstore.event.models import IndexKey, IndexSpec, IndexTerm, ValueType
from y5nstore.event.wire import build_store as build_event_store
from y5nstore.sequence.wire import build_store as build_sequencer

from ..services.box import BoxService
from ..services.contracts import BoxService as BoxServiceProtocol
from ..services.contracts import ExitService as ExitServiceProtocol
from ..services.contracts import NoteService as NoteServiceProtocol
from ..services.contracts import WorldService as WorldServiceProtocol
from ..services.exit import ExitService
from ..services.namespaces import (
    box_namespace,
    exit_namespace,
    note_namespace,
    world_namespace,
)
from ..services.note import NoteService
from ..services.world import WorldService
from ..settings import Settings


def _make_adapters(store):
    """Adapt EntityStore API to match service port protocols."""

    async def scan(namespace):
        keys, _ = await store.objects.scan(
            namespace=namespace, index_key=IndexKey("all"), value="1"
        )
        results = await store.objects.get_many(keys=keys)
        return [r for r in results if r is not None]

    async def replace(*, key, value):
        return await store.objects.replace(
            key=key, doc=value, indexes=[IndexTerm(key=IndexKey("all"), value="1")]
        )

    return scan, replace


async def setup(space: NodeSpace):

    settings = Settings.load()

    store = build_event_store(settings.storage)
    sequencer = build_sequencer(settings.sequencer)
    await sequencer.initialize()

    INDEX_ALL = IndexSpec(key=IndexKey("all"), value_type=ValueType.TEXT, unique=False)

    for ns in [world_namespace(), box_namespace(), exit_namespace(), note_namespace()]:
        await store.objects.ensure_indexes(namespace=ns, specs=[INDEX_ALL])

    scan_all, on_replace = _make_adapters(store)

    worlds = WorldService(
        on_get=store.objects.get,
        on_replace=on_replace,
        on_scan=scan_all,
        on_delete=store.objects.delete,
        on_next_id=sequencer.next_id,
    )

    boxes = BoxService(
        on_get=store.objects.get,
        on_replace=on_replace,
        on_scan=scan_all,
        on_delete=store.objects.delete,
        on_next_id=sequencer.next_id,
    )

    exits = ExitService(
        on_get=store.objects.get,
        on_replace=on_replace,
        on_scan=scan_all,
        on_delete=store.objects.delete,
        on_next_id=sequencer.next_id,
    )

    notes = NoteService(
        on_get=store.objects.get,
        on_replace=on_replace,
        on_scan=scan_all,
        on_delete=store.objects.delete,
        on_next_id=sequencer.next_id,
    )

    space.ports.provide(WorldServiceProtocol, worlds)
    space.ports.provide(BoxServiceProtocol, boxes)
    space.ports.provide(ExitServiceProtocol, exits)
    space.ports.provide(NoteServiceProtocol, notes)
