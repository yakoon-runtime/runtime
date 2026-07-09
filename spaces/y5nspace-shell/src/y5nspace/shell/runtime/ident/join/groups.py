from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.naming import Key, Namespace
from y5n.api.nodes import NodeSpace, Request

from ....models.ident import Membership, User
from ....ports import OnProject
from ....services.ident import MembershipService, Namespaces, UserService

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    namespaces = space.ports.get(Namespaces)
    users = space.ports.get(UserService)
    members = space.ports.get(MembershipService)

    async def get_user_by_name(name: str) -> User | None:
        return await users.get_by_username(
            namespace=namespaces.user_namespace(),
            username=name,
        )

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
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
        raise ValueError(f"User '{username}' not exists.")

    memberships = await on_list_user_memberships(
        namespace=namespace,
        user_key=user.key,
    )

    projection = await on_project(
        name="join/groups",
        lang=request.lang,
        state={
            "joins": memberships,
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
