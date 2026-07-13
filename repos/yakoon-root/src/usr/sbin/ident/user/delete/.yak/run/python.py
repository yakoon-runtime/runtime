from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import PROJECT

from .ports import NAMESPACES, USER_SERVICE


async def run(space: NodeSpace):
    request = space.request
    username = request.arg(0)

    namespaces = space.ports.get(NAMESPACES)
    users_svc = space.ports.get(USER_SERVICE)

    await users_svc.delete_user(
        namespace=namespaces.user_namespace(),
        username=username,
    )

    projection = await space.ports.get(PROJECT)(
        space=space,
        state={"name": username},
    )
    yield out(projection)
