from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.naming import Key, Namespace
from y5n.api.nodes import NodeSpace, Request

from ....models.ident import Group, Membership
from ....ports import OnProject
from ....services.ident import GroupService, MembershipService, Namespaces

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    namespaces = space.ports.get(Namespaces)
    groups = space.ports.get(GroupService)
    members = space.ports.get(MembershipService)

    async def get_group_by_name(name: str) -> Group | None:
        return await groups.get_by_name(
            namespace=namespaces.group_namespace(),
            name=name,
        )

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_get_namespace=namespaces.membership_namespace,
        on_list_group_memberships=members.list_group_memberships,
        on_get_group_by_name=get_group_by_name,
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
    on_list_group_memberships: OnListGroupMemberships,
):
    groupname = request.arg(0)

    namespace = on_get_namespace()
    group = await on_get_group_by_name(name=groupname)
    if not group:
        raise ValueError(f"Group '{groupname}' not exists.")

    memberships = await on_list_group_memberships(
        namespace=namespace,
        group_key=group.key,
    )

    projection = await on_project(
        name="membership/users",
        lang=request.lang,
        state={
            "memberships": memberships,
            "group": groupname,
        },
    )
    return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnGetGroupByName(Protocol):
    async def __call__(self, *, name: str) -> Group | None: ...


class OnListGroupMemberships(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        group_key: Key,
    ) -> list[Membership]: ...
