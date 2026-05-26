from __future__ import annotations

from typing import Protocol

from y5n.base.flow import out
from y5n.base.naming import Namespace
from y5n.base.nodes import NodeSpace, Request

from ...models import Group
from ...ports import OnProject
from ...services import GroupService, Namespaces

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_group_list(space: NodeSpace):

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_get_namespace=space.ports.get(Namespaces).group_namespace,
        on_list_groups=space.ports.get(GroupService).list_groups,
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
