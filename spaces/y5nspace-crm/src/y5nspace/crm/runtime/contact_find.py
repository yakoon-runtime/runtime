from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.naming import Namespace
from y5n.api.nodes import NodeSpace, Request

from ..models import Contact
from ..ports import OnProject
from ..services import ContactService, Namespaces


async def run(space: NodeSpace):

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_get_namespace=space.ports.get(Namespaces).contact_namespace,
        on_find_contacts=space.ports.get(ContactService).find_contacts,
    )


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_find_contacts: OnFindContacts,
):
    filters = {}
    for field in ("name", "company", "email", "phone", "city", "country"):
        val = request.option(field)
        if val:
            filters[field] = val

    namespace = on_get_namespace()
    contacts = await on_find_contacts(namespace=namespace, **filters)

    projection = await on_project(
        name="contact/find",
        lang=request.lang,
        state={"contacts": contacts},
    )
    return out(projection)


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnFindContacts(Protocol):
    async def __call__(self, namespace: Namespace, **filters: str) -> list[Contact]: ...
