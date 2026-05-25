from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Key, Namespace
from yakoon.base.nodes import Request, RuntimeContext
from yakoon.base.runtime.errors import DomainError

from ...models import Group, Membership
from ...ports import OnProject
from ...services import GroupService, MembershipService, Namespaces

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_membership_users(ctx: RuntimeContext):

    namespaces = ctx.ports.get(Namespaces)
    groups = ctx.ports.get(GroupService)
    members = ctx.ports.get(MembershipService)

    async def get_group_by_name(name: str) -> Group | None:
        return await groups.get_by_name(
            namespace=namespaces.group_namespace(),
            name=name,
        )

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
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
        raise DomainError(f"Group '{groupname}' not exists.")

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
