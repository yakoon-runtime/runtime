from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Key, Namespace
from yakoon.base.nodes import Request, RuntimeContext
from yakoon.base.runtime.errors import DomainError
from yakoon.ident.models import Membership, User

from ...ports import OnProject
from ...services import MembershipService, Namespaces, UserService

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_membership_groups(ctx: RuntimeContext):

    namespaces = ctx.ports.get(Namespaces)
    users = ctx.ports.get(UserService)
    members = ctx.ports.get(MembershipService)

    async def get_user_by_name(name: str) -> User | None:
        return await users.get_by_username(
            namespace=namespaces.user_namespace(),
            username=name,
        )

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        on_get_namespace=namespaces.membership_namespace,
        on_list_user_memberships=members.list_user_memberships,
        on_get_user_by_name=get_user_by_name,
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
    on_list_user_memberships: OnListUserMemberships,
):
    username = request.arg(0)

    namespace = on_get_namespace()
    user = await on_get_user_by_name(name=username)
    if not user:
        raise DomainError(f"User '{username}' not exists.")

    memberships = await on_list_user_memberships(
        namespace=namespace,
        user_key=user.key,
    )

    projection = await on_project(
        name="membership/groups",
        lang=request.lang,
        state={
            "memberships": memberships,
            "user": username,
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


class OnListUserMemberships(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
    ) -> list[Membership]: ...
