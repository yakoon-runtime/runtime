from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Namespace
from yakoon.base.nodes import NodeSpace, Request

from ...ports import OnProject
from ...services import GroupService, Namespaces

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_group_delete(space: NodeSpace):

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_get_namespace=space.ports.get(Namespaces).group_namespace,
        on_delete_group=space.ports.get(GroupService).delete_group,
    )


# ----------------------------------
# HANDLER
# ----------------------------------


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_delete_group: OnDeleteGroup,
):
    groupname = request.arg(0)

    namespace = on_get_namespace()
    await on_delete_group(
        namespace=namespace,
        name=groupname,
    )

    projection = await on_project(
        name="group/delete",
        lang=request.lang,
        state={
            "groupname": groupname,
        },
    )
    return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnDeleteGroup(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        name: str,
    ) -> None: ...
