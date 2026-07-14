from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import PROJECT

from .ports import GROUP_SERVICE, NAMESPACES


async def run(space: NodeSpace):
    namespaces = space.ports.get(NAMESPACES)
    groups_svc = space.ports.get(GROUP_SERVICE)

    namespace = namespaces.group_namespace()
    groups = await groups_svc.list_groups(namespace=namespace)

    projection = await space.ports.get(PROJECT)(
        space=space,
        state={"groups": groups},
    )
    yield out(projection)
