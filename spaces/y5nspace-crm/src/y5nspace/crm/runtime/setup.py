from __future__ import annotations

from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnProjectionResolve
from y5n.api.projections import Projection
from y5n.api.resources import ResourceRef
from y5nstore.event.wire import build_store

from ..ports import OnProject
from ..services import ContactService, Namespaces
from ..settings import Settings


async def setup(space: NodeSpace):

    settings = Settings()

    namespaces = Namespaces()

    store = build_store(settings.storage)
    await _build_index(store)

    contacts = ContactService(
        on_get=store.objects.get,
        on_append=store.objects.append,
        on_replace=store.objects.replace,
        on_get_many=store.objects.get_many,
        on_scan=store.objects.scan,
        on_delete=store.objects.delete,
        on_query_index=store.objects.query_index,
    )

    async def on_project(
        *,
        name: str,
        lang: str,
        state: dict | None = None,
    ) -> Projection:

        resource = ResourceRef(
            package="y5nspace.crm",
            path=f"resources/{lang}/templates/{name}",
        )

        on_project = space.ports.get(OnProjectionResolve)
        return await on_project(resource=resource, state=state)

    space.ports.provide(Namespaces, namespaces)
    space.ports.provide(ContactService, contacts)
    space.ports.provide(OnProject, on_project)


async def _build_index(store):

    namespaces = Namespaces()

    await store.objects.ensure_indexes(
        namespace=namespaces.contact_namespace(),
        specs=ContactService.index_specs(),
    )
