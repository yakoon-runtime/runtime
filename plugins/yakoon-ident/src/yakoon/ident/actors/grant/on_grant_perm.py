from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Namespace
from yakoon.base.nodes import Request, RuntimeContext
from yakoon.ident.models.permgrant import PermissionGrant

from ...ports import OnProject
from ...services import Namespaces, PermissionGrantService

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_grant_perm(ctx: RuntimeContext):

    namespaces = ctx.ports.get(Namespaces)
    permgrant_service = ctx.ports.get(PermissionGrantService)

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        on_get_namespace=namespaces.permgrant_namespace,
        on_list_permission_grants=permgrant_service.list_permission_grants,
    )


# ----------------------------------
# HANDLER
# ----------------------------------


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_list_permission_grants: OnListPermissionGrants,
):

    permission_key = request.arg(0)

    namespace = on_get_namespace()

    grants = await on_list_permission_grants(
        namespace=namespace,
        permission_key=permission_key,
    )

    projection = await on_project(
        name="grant/permission",
        lang=request.lang,
        state={
            "permission": permission_key,
            "grants": grants,
        },
    )
    return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnListPermissionGrants(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        permission_key: str,
    ) -> list[PermissionGrant]: ...
