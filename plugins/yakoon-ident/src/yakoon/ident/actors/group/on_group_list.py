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


async def on_group_list(ctx: RuntimeContext):

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        resource=ctx.resource,
        on_get_namespace=ctx.ports.get(Namespaces).group_namespace,
        on_list_groups=ctx.ports.get(GroupService).list_groups,
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
    on_list_groups: OnListGroups,
):
    namespace = on_get_namespace()
    groups = await on_list_groups(namespace=namespace)

    reference = await resource(
        domain="resource",
        scope="group",
        key="list",
        lang=request.lang,
    )

    projection = await on_project(
        resource=reference,
        state={
            "groups": groups,
        },
    )
    return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnListGroups(Protocol):
    async def __call__(self, namespace: Namespace) -> list[Group]: ...
