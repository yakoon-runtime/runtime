from typing import Protocol

from yakoon.base.naming import Namespace
from yakoon.base.nodes import Node, NodePath
from yakoon.base.plugins.models import AuthResult
from yakoon.base.projection import Projection
from yakoon.base.resources import ResourceRef
from yakoon.base.runtime.sessions import Session

# -------------------
# -- PLUGIN PORTS ---
# -------------------


class OnProjectionResolve(Protocol):
    async def __call__(
        self, *, resource: ResourceRef, state: dict | None = None
    ) -> Projection: ...


class OnManualResolve(Protocol):
    async def __call__(self, *, key: NodePath, lang: str) -> Projection | None: ...


class OnErrorResolve(Protocol):
    async def __call__(
        self,
        *,
        node: Node,
        session: Session,
        error: Exception,
    ) -> Projection | None: ...


class OnSessionSave(Protocol):
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
