from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Key, Namespace
from yakoon.base.nodes import Request, ResourceHandler, RuntimeContext
from yakoon.base.plugins.ports import OnProject
from yakoon.base.runtime.errors import DomainError

from ...models import Group, Membership, User
from ...services import GroupService, MembershipService, Namespaces, UserService

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_membership_remove(ctx: RuntimeContext):

    namespaces = ctx.ports.get(Namespaces)
    user_service = ctx.ports.get(UserService)
    group_service = ctx.ports.get(GroupService)
    membership_service = ctx.ports.get(MembershipService)

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
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        resource=ctx.resource,
        on_get_namespace=namespaces.membership_namespace,
        on_get_user_by_name=get_user_by_name,
        on_get_group_by_name=get_group_by_name,
        on_remove_membership=membership_service.remove_membership,
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
    on_get_user_by_name: OnGetUserByName,
    on_get_group_by_name: OnGetGroupByName,
    on_remove_membership: OnRemoveMembership,
):
    username = request.arg(0)
    groupname = request.arg(1)

    namespace = on_get_namespace()

    user = await on_get_user_by_name(name=username)
    if not user:
        raise DomainError(f"User '{username}' not exists.")

    group = await on_get_group_by_name(name=groupname)
    if not group:
        raise DomainError(f"Group '{groupname}' does not exist.")

    membership = await on_remove_membership(
        namespace=namespace,
        user_key=user.key,
        group_key=group.key,
    )

    reference = await resource(
        domain="resource",
        scope="membership",
        key="remove",
        lang=request.lang,
    )

    projection = await on_project(
        resource=reference,
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


class OnRemoveMembership(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
        group_key: Key,
    ) -> Membership: ...
