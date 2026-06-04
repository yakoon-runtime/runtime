from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.naming import Key, Namespace
from y5n.api.nodes import NodeSpace, Request
from y5n.base.runtime.errors import DomainError

from ...models import PermissionGrant, User
from ...ports import OnProject
from ...services import Namespaces, PermissionGrantService, UserService

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    namespaces = space.ports.get(Namespaces)
    user_service = space.ports.get(UserService)
    permgrant_service = space.ports.get(PermissionGrantService)

    async def get_user_by_name(name: str) -> User | None:
        return await user_service.get_by_username(
            namespace=namespaces.user_namespace(),
            username=name,
        )

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_get_namespace=namespaces.permgrant_namespace,
        on_get_user_by_name=get_user_by_name,
        on_list_subject_grants=permgrant_service.list_subject_grants,
    )


# ----------------------------------
# HANDLER
# ----------------------------------


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_get_user_by_name: OnGetUserByName,
    on_list_subject_grants: OnListSubjectGrants,
):
    username = request.arg(0)
    namespace = on_get_namespace()

    user = await on_get_user_by_name(name=username)
    if not user:
        raise DomainError(f"User '{username}' " f"does not exist.")

    grants = await on_list_subject_grants(
        namespace=namespace,
        subject_key=user.key,
    )

    projection = await on_project(
        name="grant/user",
        lang=request.lang,
        state={
            "user": username,
            "grants": grants,
        },
    )
    return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnGetUserByName(Protocol):
    async def __call__(
        self,
        *,
        name: str,
    ) -> User | None: ...


class OnListSubjectGrants(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        subject_key: Key,
    ) -> list[PermissionGrant]: ...
