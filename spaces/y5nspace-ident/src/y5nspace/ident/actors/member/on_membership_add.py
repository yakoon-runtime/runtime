from __future__ import annotations

from typing import Protocol

from y5n.base.flow import out
from y5n.base.naming import Key, Namespace
from y5n.base.nodes import NodeSpace, Request
from y5n.base.runtime.errors import DomainError

from ...models import Group, Membership, User
from ...ports import OnProject
from ...services import GroupService, MembershipService, Namespaces, UserService

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_membership_add(space: NodeSpace):

    namespaces = space.ports.get(Namespaces)
    user_service = space.ports.get(UserService)
    group_service = space.ports.get(GroupService)
    membership_service = space.ports.get(MembershipService)

    async def get_user_by_name(name: str) -> User | None:
        return await user_service.get_by_username(
            namespace=namespaces.user_namespace(),
            username=name,
        )

    async def get_group_by_name(name: str) -> Group | None:
        return await group_service.get_by_name(
            namespace=namespaces.group_namespace(),
            name=name,
        )

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_get_namespace=namespaces.membership_namespace,
        on_get_user_by_name=get_user_by_name,
        on_get_group_by_name=get_group_by_name,
        on_add_membership=membership_service.add_membership,
    )


# ----------------------------------
# HANDLER
# ----------------------------------


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_get_user_by_name: OnGetUserByName,
    on_get_group_by_name: OnGetGroupByName,
    on_add_membership: OnAddMembership,
):
    username = request.arg(0)
    groupname = request.arg(1)

    namespace = on_get_namespace()

    user = await on_get_user_by_name(name=username)
    if not user:
        raise DomainError(f"User '{username}' not exists.")

    group = await on_get_group_by_name(name=groupname)
    if not group:
        raise DomainError(f"Group '{groupname}' not exists.")

    membership = await on_add_membership(
        namespace=namespace,
        user_key=user.key,
        group_key=group.key,
    )

    projection = await on_project(
        name="membership/add",
        lang=request.lang,
        state={
            "membership": membership,
        },
    )
    return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnGetUserByName(Protocol):
    async def __call__(self, *, name: str) -> User | None: ...


class OnGetGroupByName(Protocol):
    async def __call__(self, *, name: str) -> Group | None: ...


class OnAddMembership(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
        group_key: Key,
    ) -> Membership: ...
