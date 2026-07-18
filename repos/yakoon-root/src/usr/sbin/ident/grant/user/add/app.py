from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import DOCUMENT

from .ports import NAMESPACES, PERMGRANT_SERVICE, USER_SERVICE


async def run(space: NodeSpace):
    request = space.request
    username = request.arg(0)
    permission_key = request.arg(1)
    bits = request.option("bits") or "x"
    deny = bool(request.option("deny"))

    namespaces = space.ports.get(NAMESPACES)
    users_svc = space.ports.get(USER_SERVICE)
    permgrant_svc = space.ports.get(PERMGRANT_SERVICE)

    user = await users_svc.get_by_username(
        namespace=namespaces.user_namespace(),
        username=username,
    )
    if not user:
        raise ValueError(f"User '{username}' does not exist.")

    grant = await permgrant_svc.add_grant(
        namespace=namespaces.permgrant_namespace(),
        subject_key=user.key,
        permission_key=permission_key,
        bits=bits,
        deny=deny,
    )

    projection = await space.ports.get(DOCUMENT)(
        space=space,
        state={"grant": grant},
    )
    yield out(projection)
