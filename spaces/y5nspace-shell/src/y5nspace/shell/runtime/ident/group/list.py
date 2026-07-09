from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace, Request
from y5n.api.naming import Namespace

from ....models.ident import Group
from ....ports import OnProject
from ....services.ident import GroupService, Namespaces

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

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
