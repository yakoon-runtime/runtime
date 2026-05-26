from __future__ import annotations

from typing import Protocol, cast

from y5n.base.controllers import Composer
from y5n.base.plugins.ports import (
    OnManualGet,
    OnProjectionResolve,
    OnSessionSave,
)
from y5n.base.sources import OnSourceRead

from ..commands.system import (
    CmdExit,
    CmdLs,
    CmdMan,
    CmdQuit,
    CmdUse,
    CmdVersion,
    CmdWelcome,
    SystemCommands,
)


class SystemComposer(Composer):

    command_groups = (SystemCommands,)

    # ----------------------------------
    # COMMAND FACTORIES
    # ----------------------------------

    command_factories = {
        CmdVersion: lambda self: CmdVersion(
            on_project=self.port(OnProjectionResolve),
        ),
        CmdWelcome: lambda self: CmdWelcome(
            on_project=self.port(OnProjectionResolve),
        ),
        CmdQuit: lambda self: CmdQuit(
            on_project=self.port(OnProjectionResolve),
            on_set_mark=self.access.mark,
        ),
        CmdUse: lambda self: CmdUse(
            on_source=self.port(OnSourceRead),
            on_project=self.port(OnProjectionResolve),
            on_get_active_app=self.access.get_active_app,
            on_set_active_app=self.access.set_active_app,
            on_save_session=self.save_session,
        ),
        CmdMan: lambda self: CmdMan(
            on_project=self.port(OnProjectionResolve),
            on_get_manual=self.port(OnManualGet),
            on_source=self.port(OnSourceRead),
            on_get_active_app=self.access.get_active_app,
            on_get_session=lambda: self.session,
        ),
        CmdExit: lambda self: CmdExit(
            on_source=self.port(OnSourceRead),
            on_has_interaction=self.access.has_interaction,
            on_get_active_app=self.access.get_active_app,
            on_set_active_app=self.access.set_active_app,
            on_set_interaction=self.access.set_interaction,
            on_save_session=self.save_session,
        ),
        CmdLs: lambda self: CmdLs(
            on_project=self.port(OnProjectionResolve),
            on_source=self.port(OnSourceRead),
            on_get_session=lambda: self.session,
            on_get_active_app=self.access.get_active_app,
        ),
    }

    # ----------------------------------
    # HELPERS
    # ----------------------------------

    @property
    def access(self) -> _SessionAccess:
        return cast(_SessionAccess, self.session)

    async def save_session(self):
        on_save_session = self.port(OnSessionSave)
        await on_save_session(session=self.session)


# ----------------------------------
# SESSION ACCESS
# ----------------------------------


class _SessionAccess(Protocol):

    def get_active_app(self) -> str: ...

    def set_active_app(self, app_id: str) -> None: ...

    def set_interaction(self, flow_id: str | None): ...

    def has_interaction(self) -> bool: ...

    def mark(self, name: str): ...
