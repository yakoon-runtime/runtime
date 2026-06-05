from __future__ import annotations

from typing import Protocol

from y5n.api.dsl import out
from y5n.api.naming import Key, Namespace
from y5n.api.nodes import NodeSpace, Request
from y5n.api.ports import OnAuthenticate, OnSessionSave
from y5n.api.ports.models import AuthResult

from ..ports import OnProject
from ..services import Namespaces, PermissionResolver

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    namespaces = space.ports.get(Namespaces)

    # ----------------------------------
    # PERMISSIONS
    # ----------------------------------

    async def resolve_permission(user_key: Key):
        resolver = space.ports.get(PermissionResolver)
        permissions = await resolver.resolve_user_permissions(
            grant_namespace=namespaces.permgrant_namespace(),
            membership_namespace=namespaces.membership_namespace(),
            user_key=user_key,
        )
        space.session.set_permissions(permissions)

    # ----------------------------------
    # AUTHENTICATE
    # ----------------------------------

    async def _authenticate(username: str, secret: str) -> AuthResult:
        namespace = namespaces.user_namespace()
        on_authenticate = space.ports.get(OnAuthenticate)
        return await on_authenticate(
            namespace=namespace,
            username=username,
            secret=secret,
        )

    # ----------------------------------
    # SESSION HANDLING
    # ----------------------------------

    async def _save_session():
        on_save_session = space.ports.get(OnSessionSave)
        await on_save_session(session=space.session)

    # ----------------------------------
    # HANDLER
    # ----------------------------------

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_set_identity=space.session.set_identity,
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
