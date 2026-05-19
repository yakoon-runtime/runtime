from typing import Protocol

from yakoon.base.naming import Namespace
from yakoon.base.plugins.models import AuthResult
from yakoon.base.projection import Projection
from yakoon.base.resources import ResourceRef
from yakoon.base.runtime.sessions import Session
from yakoon.platform.capabilities.permission.models.set import PermissionSet

# -------------------
# -- PLUGIN PORTS ---
# -------------------


class OnProject(Protocol):
    async def __call__(
        self, *, resource: ResourceRef, state: dict | None = None
    ) -> Projection: ...


class OnSaveSession(Protocol):
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
        permissions: PermissionSet,
    ): ...
