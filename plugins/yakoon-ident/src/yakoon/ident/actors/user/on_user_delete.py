from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Namespace
from yakoon.base.nodes import Request, RuntimeContext

from ...ports import OnProject
from ...services import Namespaces, UserService

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_user_delete(ctx: RuntimeContext):

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
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
    on_get_namespace: OnGetNamespace,
    on_delete_user: OnDeleteUser,
):
    username = request.arg(0)

    namespace = on_get_namespace()
    await on_delete_user(
        namespace=namespace,
        username=username,
    )

    projection = await on_project(
        name="user/delete",
        lang=request.lang,
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
