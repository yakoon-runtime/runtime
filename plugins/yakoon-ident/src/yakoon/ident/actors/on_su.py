from __future__ import annotations

from typing import Protocol

from yakoon.base.flow import out
from yakoon.base.naming import Key, Namespace
from yakoon.base.nodes import Request, RuntimeContext
from yakoon.base.plugins.models import AuthResult
from yakoon.base.plugins.ports import OnAuthenticate, OnSessionSave

from ..ports import OnProject
from ..services import Namespaces, PermissionResolver

# ----------------------------------
# ENTRY
# ----------------------------------


async def on_su(ctx: RuntimeContext):

    namespaces = ctx.ports.get(Namespaces)

    # ----------------------------------
    # PERMISSIONS
    # ----------------------------------

    async def resolve_permission(user_key: Key):
        resolver = ctx.ports.get(PermissionResolver)
        permissions = await resolver.resolve_user_permissions(
            grant_namespace=namespaces.permgrant_namespace(),
            membership_namespace=namespaces.membership_namespace(),
            user_key=user_key,
        )
        ctx.session.set_permissions(permissions)

    # ----------------------------------
    # AUTHENTICATE
    # ----------------------------------

    async def _authenticate(username: str, secret: str) -> AuthResult:
        namespace = namespaces.user_namespace()
        on_authenticate = ctx.ports.get(OnAuthenticate)
        return await on_authenticate(
            namespace=namespace,
            username=username,
            secret=secret,
        )

    # ----------------------------------
    # SESSION HANDLING
    # ----------------------------------

    async def _save_session():
        on_save_session = ctx.ports.get(OnSessionSave)
        await on_save_session(session=ctx.session)

    # ----------------------------------
    # HANDLER
    # ----------------------------------

    yield await _handler(
        request=ctx.request,
        on_project=ctx.ports.get(OnProject),
        on_set_identity=ctx.session.set_identity,
        on_authenticate=_authenticate,
        on_store_session=_save_session,
        on_apply_permissions=resolve_permission,
    )


# ----------------------------------
# HANDLER
# ----------------------------------


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_set_identity: OnSetIdentity,
    on_authenticate: OnAuthenticateUser,
    on_store_session: OnStoreSession,
    on_apply_permissions: OnResolvePermissions,
):

    username = request.arg(0) or request.option("user")
    secret = request.option("password")
    if not secret:
        # secret = await projector.require_first("ask_secret")
        if secret:
            secret = secret.reveal()

    result = await on_authenticate(username, secret)
    if result.ok and result.user:

        user = result.user
        user_key: Key = user["key"]

        on_set_identity(user_key)

        await on_apply_permissions(user_key=user_key)

        await on_store_session()

        projection = await on_project(
            name="su/success",
            lang=request.lang,
            state={
                "user": user["username"],
            },
        )
    else:
        projection = await on_project(
            name="su/error",
            lang=request.lang,
            state={
                "user": username,
                "reason": result.reason,
            },
        )

    return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnSetIdentity(Protocol):
    def __call__(self, user_key: Key): ...


class OnAuthenticateUser(Protocol):
    async def __call__(self, username: str, secret: str) -> AuthResult: ...


class OnStoreSession(Protocol):
    async def __call__(self): ...


class OnResolvePermissions(Protocol):
    async def __call__(
        self,
        *,
        user_key: Key,
    ): ...
