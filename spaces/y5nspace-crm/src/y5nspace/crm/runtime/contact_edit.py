from __future__ import annotations

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
        on_edit_contact=space.ports.get(ContactService).edit_contact,
    )


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_edit_contact: OnEditContact,
):
    name = request.arg(0)

    changes = {}
    for field in ("company", "email", "phone", "street", "zip", "city", "country", "notes"):
        val = request.option(field)
        if val is not None:
            changes[field] = val

    namespace = on_get_namespace()
    try:
        contact = await on_edit_contact(
            namespace=namespace,
            name=name,
            changes=changes,
        )
    except ValueError as e:
        projection = await on_project(
            name="contact/error",
            lang=request.lang,
            state={"message": str(e)},
        )
        return out(projection)

    projection = await on_project(
        name="contact/edit",
        lang=request.lang,
        state={"contact": contact},
    )
    return out(projection)


class OnGetNamespace:
    def __call__(self) -> Namespace: ...


class OnEditContact:
    async def __call__(
        self,
        *,
        namespace: Namespace,
        name: str,
        changes: dict,
    ) -> Contact: ...
