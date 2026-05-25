from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Key, Namespace
from yakoon.base.nodes import NodeSpace, Request
from yakoon.base.runtime.errors import DomainError
from yakoon.ident.models.permgrant import PermissionGrant

from ...models.group import Group
from ...ports import OnProject
from ...services import GroupService, Namespaces, PermissionGrantService

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_grant_group(space: NodeSpace):

    namespaces = space.ports.get(Namespaces)
    groups = space.ports.get(GroupService)
    permgrant_service = space.ports.get(PermissionGrantService)

    async def get_group_by_name(name: str) -> Group | None:
        return await groups.get_by_name(
            namespace=namespaces.group_namespace(),
            name=name,
        )

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
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

    projection = await on_project(
        name="grant/group",
        lang=request.lang,
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
