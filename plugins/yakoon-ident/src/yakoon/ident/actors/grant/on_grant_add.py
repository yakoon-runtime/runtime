from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Namespace
from yakoon.base.naming.key import Key
from yakoon.base.nodes import Request, ResourceHandler, RuntimeContext
from yakoon.base.plugins.ports import OnProject
from yakoon.ident.models.permgrant import PermissionGrant

from ...services import Namespaces, PermissionGrantService
from .ports import OnResolveSubject

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_grant_add(ctx: RuntimeContext):

    namespaces = ctx.ports.get(Namespaces)
    permgrant_service = ctx.ports.get(PermissionGrantService)
    resolve_subject = ctx.ports.get(OnResolveSubject)

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        resource=ctx.resource,
        on_get_namespace=namespaces.permgrant_namespace,
        on_add_grant=permgrant_service.add_grant,
        on_resolve_subject=resolve_subject,
    )


# ----------------------------------
# HANDLER
# ----------------------------------


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    resource: ResourceHandler,
    on_get_namespace: OnGetNamespace,
    on_add_grant: OnAddGrant,
    on_resolve_subject: OnResolveSubject,
):
    subject_type = request.arg(0)
    subject_name = request.arg(1)

    permission_key = request.arg(2)

    bits = request.option("bits") or "x"
    deny = bool(request.option("deny"))

    namespace = on_get_namespace()

    subject = await on_resolve_subject(
        subject_type=subject_type,
        subject_name=subject_name,
    )

    grant = await on_add_grant(
        namespace=namespace,
        subject_key=subject.key,
        permission_key=permission_key,
        bits=bits,
        deny=deny,
    )

    reference = await resource(
        domain="resource",
        scope="grant",
        key="add",
        lang=request.lang,
    )

    projection = await on_project(
        resource=reference,
        state={
            "grant": grant,
        },
    )
    return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnAddGrant(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        subject_key: Key,
        permission_key: str,
        bits: str = "x",
        deny: bool = False,
    ) -> PermissionGrant: ...
