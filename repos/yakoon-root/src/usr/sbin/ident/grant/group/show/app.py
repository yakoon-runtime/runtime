from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import DOCUMENT

from .ports import GROUP_SERVICE, NAMESPACES, PERMGRANT_SERVICE


async def run(space: NodeSpace):
    request = space.request
    groupname = request.arg(0)

    namespaces = space.ports.get(NAMESPACES)
    groups_svc = space.ports.get(GROUP_SERVICE)
    permgrant_svc = space.ports.get(PERMGRANT_SERVICE)

    group = await groups_svc.get_by_name(
        namespace=namespaces.group_namespace(),
        name=groupname,
    )
    if not group:
        raise ValueError(f"Group '{groupname}' does not exist.")

    grants = await permgrant_svc.list_subject_grants(
        namespace=namespaces.permgrant_namespace(),
        subject_key=group.key,
    )

    projection = await space.ports.get(DOCUMENT)(
        space=space,
        state={"group": groupname, "grants": grants},
    )
    yield out(projection)
