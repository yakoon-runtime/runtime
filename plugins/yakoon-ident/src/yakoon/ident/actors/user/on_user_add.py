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


async def on_user_add(ctx: RuntimeContext):

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        on_get_namespace=ctx.ports.get(Namespaces).user_namespace,
        on_add_user=ctx.ports.get(UserService).add_user,
    )


# ----------------------------------
# HANDLER
# ----------------------------------


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_add_user: OnAddUser,
):
    username = request.arg(0)
    password = request.option("password")

    namespace = on_get_namespace()
    user = await on_add_user(
        namespace=namespace,
        username=username,
        password=password,
    )

    projection = await on_project(
        name="user/add",
        lang=request.lang,
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


class OnAddUser(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        username: str,
        password: str | None,
    ) -> User: ...
