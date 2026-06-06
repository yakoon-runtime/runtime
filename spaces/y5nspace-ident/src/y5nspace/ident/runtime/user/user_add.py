from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.naming import Namespace
from y5n.api.nodes import NodeSpace, Request

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
        on_add_user=space.ports.get(UserService).add_user,
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
