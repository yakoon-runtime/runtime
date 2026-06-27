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
        on_add_contact=space.ports.get(ContactService).add_contact,
    )


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_add_contact: OnAddContact,
):
    name = request.arg(0)
    company = request.option("company") or ""
    email = request.option("email") or ""
    phone = request.option("phone") or ""
    street = request.option("street") or ""
    zip = request.option("zip") or ""
    city = request.option("city") or ""
    country = request.option("country") or ""
    notes = request.option("notes") or ""

    namespace = on_get_namespace()
    try:
        contact = await on_add_contact(
            namespace=namespace,
            name=name,
            company=company,
            email=email,
            phone=phone,
            street=street,
            zip=zip,
            city=city,
            country=country,
            notes=notes,
        )
    except ValueError as e:
        projection = await on_project(
            name="contact/error",
            lang=request.lang,
            state={"message": str(e)},
        )
        return out(projection)

    projection = await on_project(
        name="contact/add",
        lang=request.lang,
        state={"contact": contact},
    )
    return out(projection)


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnAddContact(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        name: str,
        company: str = "",
        email: str = "",
        phone: str = "",
        street: str = "",
        zip: str = "",
        city: str = "",
        country: str = "",
        notes: str = "",
    ) -> Contact: ...
