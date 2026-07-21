from __future__ import annotations

from y5n.api.naming import Namespace
from y5n.sdk import io, ports


async def main():
    users_svc = ports.get("ident.users")
    namespace = Namespace("ident", "user", "global")
    users = await users_svc.list_users(namespace=namespace)

    doc = ports.get("document")
    result = await doc.render(
        name="default",
        state={"users": users},
    )
    await io.write(result)
