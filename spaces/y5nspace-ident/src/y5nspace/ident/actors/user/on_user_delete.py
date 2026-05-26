from __future__ import annotations

from typing import Protocol

from y5n.base.flow import out
from y5n.base.naming import Namespace
from y5n.base.nodes import NodeSpace, Request

from ...ports import OnProject
from ...services import Namespaces, UserService

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_user_delete(space: NodeSpace):

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
