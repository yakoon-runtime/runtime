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


async def on_group_add(ctx: RuntimeContext):

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        on_get_namespace=ctx.ports.get(Namespaces).group_namespace,
        on_add_group=ctx.ports.get(GroupService).add_group,
    )


# ----------------------------------
# HANDLER
# ----------------------------------


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_add_group: OnAddGroup,
):
    name = request.arg(0)

    namespace = on_get_namespace()
    group = await on_add_group(
        namespace=namespace,
        name=name,
    )

    projection = await on_project(
        name="group/add",
        lang=request.lang,
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


class OnAddGroup(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        name: str,
    ) -> Group: ...
