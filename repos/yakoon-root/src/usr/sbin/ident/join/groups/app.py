from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import DOCUMENT

from .ports import JOIN_SERVICE, NAMESPACES, USER_SERVICE


async def run(space: NodeSpace):
    request = space.request
    username = request.arg(0)

    namespaces = space.ports.get(NAMESPACES)
    users_svc = space.ports.get(USER_SERVICE)
    joins_svc = space.ports.get(JOIN_SERVICE)

    user = await users_svc.get_by_username(
        namespace=namespaces.user_namespace(),
        username=username,
    )
    if not user:
        raise ValueError(f"User '{username}' not found.")

    joins = await joins_svc.list_user_joins(
        namespace=namespaces.join_namespace(),
        user_key=user.key,
    )

    projection = await space.ports.get(DOCUMENT)(
        space=space,
        state={"joins": joins, "user": username},
    )
    yield out(projection)
