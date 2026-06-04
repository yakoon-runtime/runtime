from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.naming import Key, Namespace
from y5n.api.nodes import NodeSpace, Request

from ...models import Group, PermissionGrant
from ...ports import OnProject
from ...services import GroupService, Namespaces, PermissionGrantService

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

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
        raise ValueError(f"Group '{groupname}' " f"does not exist.")

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
