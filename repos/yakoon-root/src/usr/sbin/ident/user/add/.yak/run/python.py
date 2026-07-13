from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import PROJECT

from ..ports import NAMESPACES, USER_SERVICE


async def run(space: NodeSpace):
    request = space.request

    username = request.arg(0)
    password = request.option("password")

    namespaces = space.ports.get(NAMESPACES)
    users_svc = space.ports.get(USER_SERVICE)

    user = await users_svc.add_user(
        namespace=namespaces.user_namespace(),
        username=username,
        password=password,
    )

    projection = await space.ports.get(PROJECT)(
        space=space,
        state={"user": user},
    )
    yield out(projection)
