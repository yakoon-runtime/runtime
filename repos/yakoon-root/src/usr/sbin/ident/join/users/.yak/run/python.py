from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import PROJECT

from .ports import GROUP_SERVICE, JOIN_SERVICE, NAMESPACES


async def run(space: NodeSpace):
    request = space.request
    groupname = request.arg(0)

    namespaces = space.ports.get(NAMESPACES)
    groups_svc = space.ports.get(GROUP_SERVICE)
    joins_svc = space.ports.get(JOIN_SERVICE)

    group = await groups_svc.get_by_name(
        namespace=namespaces.group_namespace(),
        name=groupname,
    )
    if not group:
        raise ValueError(f"Group '{groupname}' not found.")

    joins = await joins_svc.list_group_joins(
        namespace=namespaces.join_namespace(),
        group_key=group.key,
    )

    projection = await space.ports.get(PROJECT)(
        space=space,
        state={"joins": joins, "group": groupname},
    )
    yield out(projection)
