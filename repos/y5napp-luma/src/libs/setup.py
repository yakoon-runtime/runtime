from __future__ import annotations

from y5n.runtime.api.nodes import NodeSpace
from y5n.runtime.store.event.models import IndexKey, IndexSpec, IndexTerm, ValueType
from y5n.runtime.store.event.wire import build_store as build_event_store
from y5n.runtime.store.sequence.wire import build_store as build_sequencer

from .ports import BOX_SERVICE, EXIT_SERVICE, NOTE_SERVICE, WORLD_SERVICE
from .services import (
    BoxService,
    ExitService,
    NoteService,
    WorldService,
    box_namespace,
    exit_namespace,
    note_namespace,
    world_namespace,
)
from .settings import Settings


async def run(space: NodeSpace):

    settings = Settings.load()

    store = build_event_store(settings.storage)
    sequencer = build_sequencer(settings.sequencer)
    await sequencer.initialize()

    INDEX_ALL = IndexSpec(
        key=IndexKey("all"), value_type=ValueType.TEXT, unique=False
    )

    for ns in [
        world_namespace(),
        box_namespace(),
        exit_namespace(),
        note_namespace(),
    ]:
        await store.objects.ensure_indexes(namespace=ns, specs=[INDEX_ALL])

    async def _scan(namespace):
        keys, _ = await store.objects.scan(
            namespace=namespace, index_key=IndexKey("all"), value="1"
        )
        results = await store.objects.get_many(keys=keys)
        return [r for r in results if r is not None]

    async def _replace(*, key, doc, indexes=(), snapshot_hint=None, expected_rev=None):
        idx = list(indexes) + [IndexTerm(key=IndexKey("all"), value="1")]
        return await store.objects.replace(key=key, doc=doc, indexes=idx)

    worlds = WorldService(
        on_get=store.objects.get,
        on_replace=_replace,
        on_scan=_scan,
        on_delete=store.objects.delete,
        on_next_id=sequencer.next_id,
    )

    boxes = BoxService(
        on_get=store.objects.get,
        on_replace=_replace,
        on_scan=_scan,
        on_delete=store.objects.delete,
        on_next_id=sequencer.next_id,
    )

    exits = ExitService(
        on_get=store.objects.get,
        on_replace=_replace,
        on_scan=_scan,
        on_delete=store.objects.delete,
        on_next_id=sequencer.next_id,
    )

    notes = NoteService(
        on_get=store.objects.get,
        on_replace=_replace,
        on_scan=_scan,
        on_delete=store.objects.delete,
        on_next_id=sequencer.next_id,
    )

    space.ports.provide(WORLD_SERVICE, worlds)
    space.ports.provide(BOX_SERVICE, boxes)
    space.ports.provide(EXIT_SERVICE, exits)
    space.ports.provide(NOTE_SERVICE, notes)
