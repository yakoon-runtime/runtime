from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace, Request
from y5n.api.naming import Namespace

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
        on_delete_user=space.ports.get(UserService).delete_user,
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
