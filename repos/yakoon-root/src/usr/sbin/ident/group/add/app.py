from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import DOCUMENT

from .ports import GROUP_SERVICE, NAMESPACES


async def run(space: NodeSpace):
    request = space.request
    name = request.arg(0)

    namespaces = space.ports.get(NAMESPACES)
    groups_svc = space.ports.get(GROUP_SERVICE)

    group = await groups_svc.add_group(
        namespace=namespaces.group_namespace(),
        name=name,
    )

    projection = await space.ports.get(DOCUMENT)(
        space=space,
        state={"group": group},
    )
    yield out(projection)
