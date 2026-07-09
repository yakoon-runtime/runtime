from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.naming import Namespace
from y5n.api.nodes import NodeSpace, Request

from .....ports import OnProject
from .....services.ident import Namespaces, PermissionGrantService


async def run(space: NodeSpace):
    namespaces = space.ports.get(Namespaces)
    permgrant_service = space.ports.get(PermissionGrantService)

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_get_namespace=namespaces.permgrant_namespace,
        on_list_permission_grants=permgrant_service.list_permission_grants,
    )


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
        name="grant/permission/show",
        lang=request.lang,
        state={
            "permission": permission_key,
            "grants": grants,
        },
    )
    return out(projection)


class OnGetNamespace:
    def __call__(self) -> Namespace: ...


class OnListPermissionGrants:
    async def __call__(self, *, namespace: Namespace, permission_key: str): ...
