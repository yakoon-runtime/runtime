from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Namespace
from yakoon.base.nodes import Request, RuntimeContext

from ...models import Group
from ...ports import OnProject
from ...services import GroupService, Namespaces

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_group_list(ctx: RuntimeContext):

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
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
    on_get_namespace: OnGetNamespace,
    on_list_groups: OnListGroups,
):
    namespace = on_get_namespace()
    groups = await on_list_groups(namespace=namespace)

    projection = await on_project(
        name="group/list",
        lang=request.lang,
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
