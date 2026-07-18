from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import DOCUMENT

from .ports import NAMESPACES, PERMGRANT_SERVICE


async def run(space: NodeSpace):
    request = space.request
    permission_key = request.arg(0)

    namespaces = space.ports.get(NAMESPACES)
    permgrant_svc = space.ports.get(PERMGRANT_SERVICE)

    grants = await permgrant_svc.list_permission_grants(
        namespace=namespaces.permgrant_namespace(),
        permission_key=permission_key,
    )

    projection = await space.ports.get(DOCUMENT)(
        space=space,
        state={"permission": permission_key, "grants": grants},
    )
    yield out(projection)
