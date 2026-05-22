from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Namespace
from yakoon.base.nodes import Request, ResourceHandler, RuntimeContext
from yakoon.base.plugins.ports import OnProject

from ...services import GroupService, Namespaces

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_group_delete(ctx: RuntimeContext):

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        resource=ctx.resource,
        on_get_namespace=ctx.ports.get(Namespaces).group_namespace,
        on_delete_group=ctx.ports.get(GroupService).delete_group,
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
    on_delete_group: OnDeleteGroup,
):
    groupname = request.arg(0)

    namespace = on_get_namespace()
    await on_delete_group(
        namespace=namespace,
        name=groupname,
    )

    reference = await resource(
        domain="resource",
        scope="group",
        key="delete",
        lang=request.lang,
    )

    projection = await on_project(
        resource=reference,
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
