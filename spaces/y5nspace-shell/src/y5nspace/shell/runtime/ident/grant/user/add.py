from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.naming import Key, Namespace
from y5n.api.nodes import NodeSpace, Request

from .....models.ident import PermissionGrant
from .....ports import OnProject
from .....services.ident import Namespaces, PermissionGrantService, UserService


async def run(space: NodeSpace):
    namespaces = space.ports.get(Namespaces)
    user_service = space.ports.get(UserService)
    permgrant_service = space.ports.get(PermissionGrantService)

    async def get_user(name: str):
        return await user_service.get_by_username(
            namespace=namespaces.user_namespace(),
            username=name,
        )

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_get_namespace=namespaces.permgrant_namespace,
        on_add_grant=permgrant_service.add_grant,
        on_get_user=get_user,
    )


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_add_grant: OnAddGrant,
    on_get_user: OnGetUser,
):
    username = request.arg(0)
    permission_key = request.arg(1)
    bits = request.option("bits") or "x"
    deny = bool(request.option("deny"))

    namespace = on_get_namespace()

    user = await on_get_user(name=username)
    if not user:
        raise ValueError(f"User '{username}' does not exist.")

    grant = await on_add_grant(
        namespace=namespace,
        subject_key=user.key,
        permission_key=permission_key,
        bits=bits,
        deny=deny,
    )

    projection = await on_project(
        name="grant/user/add",
        lang=request.lang,
        state={
            "grant": grant,
        },
    )
    return out(projection)


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnGetUser(Protocol):
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
