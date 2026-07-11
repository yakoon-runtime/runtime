from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from y5n.base.naming import Namespace
from y5n.base.nodes import NodePath, NodeSpace
from y5n.base.permissions import Permission, PermissionSet
from y5n.base.projection import Projection
from y5n.base.resources import ResourceRef
from y5n.base.runtime.sessions import Session


@dataclass(frozen=True, slots=True)
class AuthResult:
    ok: bool
    user: dict | None = None
    reason: str | None = None


# -------------------
# -- PLUGIN PORTS ---
# -------------------


class OnProjectionResolve(Protocol):
    async def __call__(
        self, *, resource: ResourceRef, state: dict | None = None
    ) -> Projection: ...


class OnProject(Protocol):
    """Resolve a projection from a node's resources.

    Uses the pre-assembled resource paths on the space to find
    the template, renders it via Jinja, and compiles it into
    a Projection.  The optional *resource* parameter selects
    which resource type to use (defaults to ``"projection"``).
    """

    async def __call__(
        self,
        *,
        space: NodeSpace,
        resource: str = "projection",
        state: dict | None = None,
    ) -> Projection: ...


class OnManualResolve(Protocol):
    async def __call__(
        self,
        *,
        key: NodePath,
        lang: str,
    ) -> Projection | None: ...


class OnErrorResolve(Protocol):
    async def __call__(
        self,
        *,
        key: NodePath,
        session: Session,
        error: Exception,
    ) -> Projection: ...


class OnSessionSave(Protocol):
    async def __call__(self, *, session: Session): ...


class OnSessionAttach(Protocol):
    async def __call__(self, *, session: Session, target_key: str): ...


class OnSessionDetach(Protocol):
    async def __call__(self, *, session: Session): ...


class OnAuthorizeRead(Protocol):
    def __call__(self, session: Session, perm_key: str) -> bool: ...


class OnAuthorizeWrite(Protocol):
    def __call__(self, session: Session, perm_key: str) -> bool: ...


class OnAuthenticate(Protocol):
    async def __call__(
        self, *, namespace: Namespace, username: str, secret: str
    ) -> AuthResult: ...


class OnBootstrapPermissions(Protocol):
    def __call__(
        self,
        *,
        session: Session,
        permissions,
    ): ...


class OnNewPermissionSet(Protocol):
    def __call__(self) -> PermissionSet: ...


class OnParsePermissionSpec(Protocol):
    def __call__(self, *, spec: str) -> Permission: ...


# ------------------
# -- PROJECTIONS ---
# ------------------


class OnResourceLoad(Protocol):
    def __call__(
        self,
        *,
        resource: ResourceRef,
    ) -> str: ...


class OnJinjaRender(Protocol):
    def __call__(self, content: str, *, context: dict) -> str: ...


class OnCompile(Protocol):
    def __call__(self, *, text: str, context: dict) -> Projection: ...
