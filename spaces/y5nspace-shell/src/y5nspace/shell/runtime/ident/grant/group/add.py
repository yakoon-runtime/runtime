from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.naming import Key, Namespace
from y5n.api.nodes import NodeSpace, Request

from .....models.ident import PermissionGrant
from .....ports import OnProject
from .....services.ident import GroupService, Namespaces, PermissionGrantService


async def run(space: NodeSpace):
    namespaces = space.ports.get(Namespaces)
    group_service = space.ports.get(GroupService)
    permgrant_service = space.ports.get(PermissionGrantService)

    async def get_group(name: str):
        return await group_service.get_by_name(
            namespace=namespaces.group_namespace(),
            name=name,
        )

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_get_namespace=namespaces.permgrant_namespace,
        on_add_grant=permgrant_service.add_grant,
        on_get_group=get_group,
    )


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_add_grant: OnAddGrant,
    on_get_group: OnGetGroup,
):
    groupname = request.arg(0)
    permission_key = request.arg(1)
    bits = request.option("bits") or "x"
    deny = bool(request.option("deny"))

    namespace = on_get_namespace()

    group = await on_get_group(name=groupname)
    if not group:
        raise ValueError(f"Group '{groupname}' does not exist.")

    grant = await on_add_grant(
        namespace=namespace,
        subject_key=group.key,
        permission_key=permission_key,
        bits=bits,
        deny=deny,
    )

    projection = await on_project(
        name="grant/group/add",
        lang=request.lang,
        state={
            "grant": grant,
        },
    )
    return out(projection)


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnGetGroup(Protocol):
    async def __call__(self, *, name: str): ...


class OnAddGrant(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        subject_key: Key,
        permission_key: str,
        bits: str = "x",
        deny: bool = False,
    ) -> PermissionGrant: ...
