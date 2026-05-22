from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Namespace
from yakoon.base.nodes import Request, ResourceHandler, RuntimeContext
from yakoon.base.plugins.ports import OnProject

from ...services import Namespaces, UserService

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_user_delete(ctx: RuntimeContext):

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        resource=ctx.resource,
        on_get_namespace=ctx.ports.get(Namespaces).user_namespace,
        on_delete_user=ctx.ports.get(UserService).delete_user,
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
    on_delete_user: OnDeleteUser,
):
    username = request.arg(0)

    namespace = on_get_namespace()
    await on_delete_user(
        namespace=namespace,
        username=username,
    )

    reference = await resource(
        domain="resource",
        scope="user",
        key="delete",
        lang=request.lang,
    )

    projection = await on_project(
        resource=reference,
        state={
            "username": username,
        },
    )
    return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnDeleteUser(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        username: str,
    ) -> None: ...
