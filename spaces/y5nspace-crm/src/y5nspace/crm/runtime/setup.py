from __future__ import annotations

from y5n.api.invocations import InvocationInput
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnPrepareInput, OnProjectionResolve
from y5n.api.projections import Projection
from y5n.api.resources import ResourceRef
from y5nstore.event.wire import build_store
from y5nstore.sequence.wire import build_store as build_sequencer

from ..ports import OnProject
from ..services import ContactService, Namespaces
from ..settings import Settings


async def setup(space: NodeSpace):

    settings = Settings.load()

    namespaces = Namespaces()

    store = build_store(settings.storage)
    await _build_index(store)

    sequencer = build_sequencer(settings.sequencer)
    await sequencer.initialize()

    contacts = ContactService(
        on_get=store.objects.get,
        on_append=store.objects.append,
        on_replace=store.objects.replace,
        on_get_many=store.objects.get_many,
        on_scan=store.objects.scan,
        on_delete=store.objects.delete,
        on_query_index=store.objects.query_index,
        on_next_id=sequencer.next_id,
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

    async def on_prepare_input(*, node, invocation, tokens, session):
        if node.key != "edit":
            return None

        name = tokens[0] if tokens else None
        if name is None:
            return None

        contact = await contacts.get_by_name(namespaces.contact_namespace(), name)
        if contact is None:
            return None

        return InvocationInput(
            values={
                "name": contact.name,
                "company": contact.data.company,
                "email": contact.data.email,
                "phone": contact.data.phone,
                "street": contact.data.street,
                "zip": contact.data.zip,
                "city": contact.data.city,
                "country": contact.data.country,
                "notes": contact.data.notes,
            }
        )

    space.ports.provide(OnPrepareInput, on_prepare_input)


async def _build_index(store):

    namespaces = Namespaces()

    await store.objects.ensure_indexes(
        namespace=namespaces.contact_namespace(),
        specs=ContactService.index_specs(),
    )
