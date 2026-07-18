from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import DOCUMENT

from .ports import NAMESPACES, USER_SERVICE


async def run(space: NodeSpace):
    namespaces = space.ports.get(NAMESPACES)
    users_svc = space.ports.get(USER_SERVICE)

    namespace = namespaces.user_namespace()
    users = await users_svc.list_users(namespace=namespace)

    projection = await space.ports.get(DOCUMENT)(
        space=space,
        state={"users": users},
    )
    yield out(projection)
