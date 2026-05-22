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


async def on_user_edit(ctx: RuntimeContext):

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        resource=ctx.resource,
        on_get_namespace=ctx.ports.get(Namespaces).user_namespace,
        on_edit_user=ctx.ports.get(UserService).edit_user,
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
    on_edit_user: OnEditUser,
):
    username = request.arg(0)

    namespace = on_get_namespace()
    changes = {
        "password": request.option("password"),
        "enabled": request.option("enabled"),
    }

    user = await on_edit_user(
        namespace=namespace,
        username=username,
        changes=changes,
    )

    reference = await resource(
        domain="resource",
        scope="user",
        key="edit",
        lang=request.lang,
    )

    projection = await on_project(
        resource=reference,
        state={
            "user": user,
        },
    )
    return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnEditUser(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        username: str,
        changes: dict,
    ) -> User: ...
