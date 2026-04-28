from collections.abc import Sequence
from typing import Protocol

from yakoon.base.application import Application
from yakoon.base.commands import Command
from yakoon.base.commands.types import CommandKind
from yakoon.base.projection import Projection
from yakoon.base.resources import ResourceRef
from yakoon.base.runtime.sessions import Session

# ----------------------------------
# PLUGIN PORTS
# ----------------------------------


class OnProject(Protocol):
    async def __call__(
        self, *, resource: ResourceRef, state: dict | None = None
    ) -> Projection: ...


class OnGetShell(Protocol):
    def __call__(self) -> Application: ...


class OnGetApp(Protocol):
    def __call__(self, *, app_id: str) -> Application | None: ...


class OnListApps(Protocol):
    def __call__(self) -> Sequence[Application]: ...


class OnListListedApps(Protocol):
    def __call__(self) -> Sequence[Application]: ...


class OnCheckAppListed(Protocol):
    def __call__(self, app_id: str) -> bool: ...


class OnSaveSession(Protocol):
    async def __call__(self, *, session: Session): ...


class OnListCommandsForApp(Protocol):
    def __call__(self, app_id: str) -> Sequence[type[Command]]: ...


class OnListCommandsForManual(Protocol):
    def __call__(
        self,
        app_id: str,
        session: Session,
        mode: str,
        kind_filter: CommandKind | None = None,
    ) -> Sequence[type[Command]]: ...
