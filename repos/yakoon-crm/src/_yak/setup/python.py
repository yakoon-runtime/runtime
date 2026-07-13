from __future__ import annotations

from y5n.api.nodes import NodeSpace
from y5nstore.event.wire import build_store
from y5nstore.sequence.wire import build_store as build_sequencer

from .ports import CONTACT_SERVICE, NAMESPACES
from .services import ContactService, Namespaces
from .settings import Settings


async def run(space: NodeSpace):
    settings = Settings.load()
    namespaces = Namespaces()
    store = build_store(settings.storage)
    sequencer = build_sequencer(settings.sequencer)
    await sequencer.initialize()

    for spec in ContactService.index_specs():
        await store.objects.ensure_indexes(namespace=namespaces.contact_namespace(), specs=[spec])

    contacts = ContactService(
        on_get=store.objects.get,
        on_replace=store.objects.replace,
        on_get_many=store.objects.get_many,
        on_scan=store.objects.scan,
        on_delete=store.objects.delete,
        on_query_index=store.objects.query_index,
        on_next_id=sequencer.next_id,
    )

    space.ports.provide(CONTACT_SERVICE, contacts)
    space.ports.provide(NAMESPACES, namespaces)
