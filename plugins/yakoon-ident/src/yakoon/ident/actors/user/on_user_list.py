from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Namespace
from yakoon.base.nodes import Request, ResourceHandler, RuntimeContext
from yakoon.base.plugins.ports import OnProject

from ...models import User
from ...services import Namespaces, UserService

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_user_list(ctx: RuntimeContext):

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        resource=ctx.resource,
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
    resource: ResourceHandler,
    on_get_namespace: OnGetNamespace,
    on_list_users: OnListUsers,
):
    namespace = on_get_namespace()
    users = await on_list_users(namespace=namespace)

    reference = await resource(
        domain="resource",
        scope="user",
        key="list",
        lang=request.lang,
    )

    projection = await on_project(
        resource=reference,
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
