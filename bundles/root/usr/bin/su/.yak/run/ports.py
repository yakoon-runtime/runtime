from typing import Protocol

from y5n.api.naming import Key, Namespace
from y5n.api.permissions import PermissionSet
from y5n.api.ports import Port


class OnPermissionResolve(Protocol):

    async def resolve_user_permissions(
        self,
        *,
        grant_namespace: Namespace,
        join_namespace: Namespace,
        user_key: Key,
    ) -> PermissionSet: ...


PERMISSION_RESOLVE = Port(
    "permission.resolve",
    protocol=OnPermissionResolve,
)
