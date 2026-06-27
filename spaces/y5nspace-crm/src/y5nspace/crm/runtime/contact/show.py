from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.naming import Namespace
from y5n.api.nodes import NodeSpace, Request

from ...models import Contact
from ...ports import OnProject
from ...services import ContactService, Namespaces


async def run(space: NodeSpace):

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_get_namespace=space.ports.get(Namespaces).contact_namespace,
        on_get_contact=space.ports.get(ContactService).get_by_name,
    )


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_get_contact: OnGetContact,
):
    name = request.arg(0)

    namespace = on_get_namespace()
    contact = await on_get_contact(namespace=namespace, name=name)
    if not contact:
        projection = await on_project(
            name="contact/not_found",
            lang=request.lang,
            state={"name": name},
        )
        return out(projection)

    projection = await on_project(
        name="contact/show",
        lang=request.lang,
        state={"contact": contact},
    )
    return out(projection)


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnGetContact(Protocol):
    async def __call__(self, *, namespace: Namespace, name: str) -> Contact | None: ...
