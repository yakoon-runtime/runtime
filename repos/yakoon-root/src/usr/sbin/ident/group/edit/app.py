from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import DOCUMENT

from .ports import GROUP_SERVICE, NAMESPACES


async def run(space: NodeSpace):
    request = space.request

    groupname = request.arg(0)
    changes = {
        "enabled": request.option("enabled"),
    }

    namespaces = space.ports.get(NAMESPACES)
    groups_svc = space.ports.get(GROUP_SERVICE)

    group = await groups_svc.edit_group(
        namespace=namespaces.group_namespace(),
        name=groupname,
        changes=changes,
    )

    projection = await space.ports.get(DOCUMENT)(
        space=space,
        state={"group": group},
    )
    yield out(projection)
