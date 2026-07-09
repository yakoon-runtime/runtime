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
        on_add_group=space.ports.get(GroupService).add_group,
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
