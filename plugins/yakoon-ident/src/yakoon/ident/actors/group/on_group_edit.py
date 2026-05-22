from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Namespace
from yakoon.base.nodes import Request, ResourceHandler, RuntimeContext
from yakoon.base.plugins.ports import OnProject

from ...models import Group
from ...services import GroupService, Namespaces

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_group_edit(ctx: RuntimeContext):

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        resource=ctx.resource,
        on_get_namespace=ctx.ports.get(Namespaces).group_namespace,
        on_edit_group=ctx.ports.get(GroupService).edit_group,
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
    on_edit_group: OnEditGroup,
):
    groupname = request.arg(0)

    namespace = on_get_namespace()
    changes = {
        "enabled": request.option("enabled"),
    }

    group = await on_edit_group(
        namespace=namespace,
        name=groupname,
        changes=changes,
    )

    reference = await resource(
        domain="resource",
        scope="group",
        key="edit",
        lang=request.lang,
    )

    projection = await on_project(
        resource=reference,
        state={
            "group": group,
        },
    )
    return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnEditGroup(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        name: str,
        changes: dict,
    ) -> Group: ...
