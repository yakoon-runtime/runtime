from __future__ import annotations

from typing import Protocol

from y5n.base.flow import out
from y5n.base.naming import Namespace
from y5n.base.nodes import NodeSpace, Request

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
        on_edit_user=space.ports.get(UserService).edit_user,
    )


# ----------------------------------
# HANDLER
# ----------------------------------


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
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

    projection = await on_project(
        name="user/edit",
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


class OnEditUser(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        username: str,
        changes: dict,
    ) -> User: ...
