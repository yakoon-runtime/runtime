from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import PROJECT

from .ports import GROUP_SERVICE, NAMESPACES


async def run(space: NodeSpace):
    request = space.request
    groupname = request.arg(0)

    namespaces = space.ports.get(NAMESPACES)
    groups_svc = space.ports.get(GROUP_SERVICE)

    await groups_svc.delete_group(
        namespace=namespaces.group_namespace(),
        name=groupname,
    )

    projection = await space.ports.get(PROJECT)(
        space=space,
        state={"name": groupname},
    )
    yield out(projection)
