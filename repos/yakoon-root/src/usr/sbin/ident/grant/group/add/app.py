from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import PROJECT

from .ports import GROUP_SERVICE, NAMESPACES, PERMGRANT_SERVICE


async def run(space: NodeSpace):
    request = space.request
    groupname = request.arg(0)
    permission_key = request.arg(1)
    bits = request.option("bits") or "x"
    deny = bool(request.option("deny"))

    namespaces = space.ports.get(NAMESPACES)
    groups_svc = space.ports.get(GROUP_SERVICE)
    permgrant_svc = space.ports.get(PERMGRANT_SERVICE)

    group = await groups_svc.get_by_name(
        namespace=namespaces.group_namespace(),
        name=groupname,
    )
    if not group:
        raise ValueError(f"Group '{groupname}' does not exist.")

    grant = await permgrant_svc.add_grant(
        namespace=namespaces.permgrant_namespace(),
        subject_key=group.key,
        permission_key=permission_key,
        bits=bits,
        deny=deny,
    )

    projection = await space.ports.get(PROJECT)(
        space=space,
        state={"grant": grant},
    )
    yield out(projection)
