from __future__ import annotations

from typing import Protocol

from y5n.runtime.api.nodes import NodePath, NodeSpace
from y5n.runtime.api.permissions import Permission, PermissionSet
from y5n.runtime.api.resources import ResourceRef
from y5n.runtime.api.runtime.sessions import Session
from y5n.runtime.api.sources import DataRequest, DataResult
from y5n.runtime.api.sources.source import DataSource

from .models import AuthResult, HealthResult

# -------------------
# -- PLUGIN PORTS ---
# -------------------


class OnDocumentResolve(Protocol):
    async def __call__(
        self, *, resource: ResourceRef, state: dict | None = None
    ) -> dict: ...


class OnProject(Protocol):
    """Resolve a document from a node's resources.

    Uses the pre-assembled resource paths on the space to find
    the template, renders it via Jinja, and compiles it into
    a Document.  The optional *resource* parameter selects
    which resource type to use (defaults to ``"document"``).
    """

    async def __call__(
        self,
        *,
        space: NodeSpace,
        resource: str = "document",
        state: dict | None = None,
    ) -> dict: ...


class OnManualResolve(Protocol):
    async def __call__(
        self,
        *,
        key: NodePath,
        lang: str,
    ) -> dict | None: ...


class OnErrorResolve(Protocol):
    async def __call__(
        self,
        *,
        key: NodePath,
        session: Session,
        error: Exception,
    ) -> dict: ...


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
        self, *, space: NodeSpace, username: str, secret: str
    ) -> AuthResult: ...


class OnAfterVerify(Protocol):
    async def __call__(self, *, user: object) -> dict | None: ...


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
# -- DOCUMENTS ---
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
    def __call__(self, *, text: str, context: dict) -> dict: ...


class OnSourceRead(Protocol):
    async def __call__(self, request: DataRequest) -> DataResult: ...


class OnDataBind(Protocol):
    def __call__(self, source: str, provider: DataSource): ...


class OnValidate(Protocol):
    def __call__(self) -> HealthResult: ...
