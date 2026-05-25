from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Namespace
from yakoon.base.naming.key import Key
from yakoon.base.nodes import Request, RuntimeContext
from yakoon.base.runtime.errors import DomainError
from yakoon.ident.models.permgrant import PermissionGrant

from ...models import User
from ...ports import OnProject
from ...services import Namespaces, PermissionGrantService, UserService

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_grant_user(ctx: RuntimeContext):

    namespaces = ctx.ports.get(Namespaces)
    user_service = ctx.ports.get(UserService)
    permgrant_service = ctx.ports.get(PermissionGrantService)

    async def get_user_by_name(name: str) -> User | None:
        return await user_service.get_by_username(
            namespace=namespaces.user_namespace(),
            username=name,
        )

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
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
