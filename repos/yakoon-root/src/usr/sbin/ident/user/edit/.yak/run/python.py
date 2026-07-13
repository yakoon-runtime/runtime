from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import PROJECT

from ..ports import USER_SERVICE, NAMESPACES


async def run(space: NodeSpace):
    request = space.request

    username = request.arg(0)
    changes = {
        "password": request.option("password"),
        "enabled": request.option("enabled"),
    }

    namespaces = space.ports.get(NAMESPACES)
    users_svc = space.ports.get(USER_SERVICE)

    user = await users_svc.edit_user(
        namespace=namespaces.user_namespace(),
        username=username,
        changes=changes,
    )

    projection = await space.ports.get(PROJECT)(
        space=space,
        state={"user": user},
    )
    yield out(projection)
