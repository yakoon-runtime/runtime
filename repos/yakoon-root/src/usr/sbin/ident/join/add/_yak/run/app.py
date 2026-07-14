from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import PROJECT

from .ports import GROUP_SERVICE, JOIN_SERVICE, NAMESPACES, USER_SERVICE


async def run(space: NodeSpace):
    request = space.request
    username = request.arg(0)
    groupname = request.arg(1)

    namespaces = space.ports.get(NAMESPACES)
    users_svc = space.ports.get(USER_SERVICE)
    groups_svc = space.ports.get(GROUP_SERVICE)
    joins_svc = space.ports.get(JOIN_SERVICE)

    user = await users_svc.get_by_username(
        namespace=namespaces.user_namespace(),
        username=username,
    )
    if not user:
        raise ValueError(f"User '{username}' not found.")

    group = await groups_svc.get_by_name(
        namespace=namespaces.group_namespace(),
        name=groupname,
    )
    if not group:
        raise ValueError(f"Group '{groupname}' not found.")

    join_obj = await joins_svc.add_join(
        namespace=namespaces.join_namespace(),
        user_key=user.key,
        group_key=group.key,
    )

    projection = await space.ports.get(PROJECT)(
        space=space,
        state={"join": join_obj},
    )
    yield out(projection)
