from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.naming import Key, Namespace
from y5n.api.nodes import NodeSpace, Request

from ....models.ident import Join, User
from ....ports import OnProject
from ....services.ident import JoinService, Namespaces, UserService

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    namespaces = space.ports.get(Namespaces)
    user_service = space.ports.get(UserService)
    join_service = space.ports.get(JoinService)

    async def get_user_by_name(name: str) -> User | None:
        return await user_service.get_by_username(
            namespace=namespaces.user_namespace(),
            username=name,
        )

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_get_namespace=namespaces.join_namespace,
        on_list_user_joins=join_service.list_user_joins,
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
    on_list_user_joins: OnListUserJoins,
):
    username = request.arg(0)

    namespace = on_get_namespace()
    user = await on_get_user_by_name(name=username)
    if not user:
        raise ValueError(f"User '{username}' not exists.")

    joins = await on_list_user_joins(
        namespace=namespace,
        user_key=user.key,
    )

    projection = await on_project(
        name="join/groups",
        lang=request.lang,
        state={
            "joins": joins,
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


class OnListUserJoins(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
    ) -> list[Join]: ...
