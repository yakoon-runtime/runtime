from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import DOCUMENT

from .ports import NAMESPACES, PERMGRANT_SERVICE, USER_SERVICE


async def run(space: NodeSpace):
    request = space.request
    username = request.arg(0)

    namespaces = space.ports.get(NAMESPACES)
    users_svc = space.ports.get(USER_SERVICE)
    permgrant_svc = space.ports.get(PERMGRANT_SERVICE)

    user = await users_svc.get_by_username(
        namespace=namespaces.user_namespace(),
        username=username,
    )
    if not user:
        raise ValueError(f"User '{username}' does not exist.")

    grants = await permgrant_svc.list_subject_grants(
        namespace=namespaces.permgrant_namespace(),
        subject_key=user.key,
    )

    projection = await space.ports.get(DOCUMENT)(
        space=space,
        state={"user": username, "grants": grants},
    )
    yield out(projection)
