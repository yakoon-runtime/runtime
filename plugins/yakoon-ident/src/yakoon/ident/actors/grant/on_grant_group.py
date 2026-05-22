from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Key, Namespace
from yakoon.base.nodes import Request, ResourceHandler, RuntimeContext
from yakoon.base.plugins.ports import OnProject
from yakoon.base.runtime.errors import DomainError
from yakoon.ident.models.permgrant import PermissionGrant

from ...models.group import Group
from ...services import GroupService, Namespaces, PermissionGrantService

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_grant_group(ctx: RuntimeContext):

    namespaces = ctx.ports.get(Namespaces)
    groups = ctx.ports.get(GroupService)
    permgrant_service = ctx.ports.get(PermissionGrantService)

    async def get_group_by_name(name: str) -> Group | None:
        return await groups.get_by_name(
            namespace=namespaces.group_namespace(),
            name=name,
        )

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        resource=ctx.resource,
        on_get_namespace=namespaces.membership_namespace,
        on_get_group_by_name=get_group_by_name,
        on_list_subject_grants=permgrant_service.list_subject_grants,
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
    on_get_group_by_name: OnGetGroupByName,
    on_list_subject_grants: OnListSubjectGrants,
):

    groupname = request.arg(0)

    namespace = on_get_namespace()
    group = await on_get_group_by_name(name=groupname)
    if not group:
        raise DomainError(f"Group '{groupname}' " f"does not exist.")

    grants = await on_list_subject_grants(
        namespace=namespace,
        subject_key=group.key,
    )

    reference = await resource(
        domain="resource",
        scope="grant",
        key="group",
        lang=request.lang,
    )

    projection = await on_project(
        resource=reference,
        state={
            "group": groupname,
            "grants": grants,
        },
    )
    return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnGetGroupByName(Protocol):
    async def __call__(
        self,
        *,
        name: str,
    ) -> Group | None: ...


class OnListSubjectGrants(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        subject_key: Key,
    ) -> list[PermissionGrant]: ...
