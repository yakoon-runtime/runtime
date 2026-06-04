from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace, Request
from y5n.api.naming import Namespace

from ...models import User
from ...ports import OnProject
from ...services import Namespaces, UserService

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_get_namespace=space.ports.get(Namespaces).user_namespace,
        on_list_users=space.ports.get(UserService).list_users,
    )


# ----------------------------------
# HANDLER
# ----------------------------------


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_list_users: OnListUsers,
):
    namespace = on_get_namespace()
    users = await on_list_users(namespace=namespace)

    projection = await on_project(
        name="user/list",
        lang=request.lang,
        state={
            "users": users,
        },
    )
    return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnListUsers(Protocol):
    async def __call__(self, namespace: Namespace) -> list[User]: ...
