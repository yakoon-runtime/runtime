from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Namespace
from yakoon.base.nodes import Request, RuntimeContext

from ...models import User
from ...ports import OnProject
from ...services import Namespaces, UserService

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_user_list(ctx: RuntimeContext):

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        on_get_namespace=ctx.ports.get(Namespaces).user_namespace,
        on_list_users=ctx.ports.get(UserService).list_users,
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
