from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.naming import Namespace
from y5n.api.nodes import NodeSpace, Request

from ..ports import OnProject
from ..services import ContactService, Namespaces


async def run(space: NodeSpace):

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_get_namespace=space.ports.get(Namespaces).contact_namespace,
        on_delete_contact=space.ports.get(ContactService).delete_contact,
    )


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_delete_contact: OnDeleteContact,
):
    name = request.arg(0)

    namespace = on_get_namespace()
    try:
        await on_delete_contact(namespace=namespace, name=name)
    except ValueError as e:
        projection = await on_project(
            name="contact/error",
            lang=request.lang,
            state={"message": str(e)},
        )
        return out(projection)

    projection = await on_project(
        name="contact/delete",
        lang=request.lang,
        state={"name": name},
    )
    return out(projection)


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnDeleteContact(Protocol):
    async def __call__(self, *, namespace: Namespace, name: str) -> None: ...
