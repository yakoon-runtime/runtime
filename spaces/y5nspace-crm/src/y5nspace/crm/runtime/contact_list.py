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
        on_list_contacts=space.ports.get(ContactService).list_contacts,
    )


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_list_contacts: OnListContacts,
):
    namespace = on_get_namespace()
    contacts = await on_list_contacts(namespace=namespace)

    projection = await on_project(
        name="contact/list",
        lang=request.lang,
        state={"contacts": contacts},
    )
    return out(projection)


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnListContacts(Protocol):
    async def __call__(self, *, namespace: Namespace) -> list[Contact]: ...
