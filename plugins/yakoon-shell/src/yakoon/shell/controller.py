from __future__ import annotations

from typing import Protocol, cast

from yakoon.base.commands import Command
from yakoon.base.controllers import Controller, ResourceReferences
from yakoon.base.plugins.ports import OnGetShell, OnSaveSession
from yakoon.shell.commands.core import CmdExit, CmdVersion, CmdWelcome

from .commands.core.cmdset import ShellSystemCommands


class ShellCoreController(Controller):

    id: str = "shell-core-controller"

    commandsets = (ShellSystemCommands,)

    resources = ResourceReferences(
        package="yakoon.shell",
    )

    command_builders: dict[type[Command], str] = {
        CmdExit: "_create_exit",
        CmdVersion: "_create_version",
        CmdWelcome: "_create_welcome",
    }

    # ----------------------------------
    # CREATE COMMAND
    # ----------------------------------

    def create_command(
        self,
    ) -> Command:
        name = self.command_builders.get(self.command)
        if name:
            return getattr(self, name)()

        raise RuntimeError("invalid command")

    # ----------------------------------
    # FACTORY
    # ----------------------------------
    def _create_version(self):
        return CmdVersion(on_project=self.project)

    def _create_welcome(self):
        return CmdWelcome(on_project=self.project)

    def _create_exit(self):
        access = cast(_SessionAccess, self.session)

        async def save_session():
            on_save_session = self.ports.on_get_port(OnSaveSession)
            await on_save_session(session=self.session)

        return CmdExit(
            on_get_shell=self.ports.on_get_port(OnGetShell),
            on_has_interaction=access.has_interaction,
            on_get_active_app=access.get_active_app,
            on_set_active_app=access.set_active_app,
            on_set_interaction=access.set_interaction,
            on_save_session=save_session,
        )


# ----------------------------------
# SESSION ACCESS
# ----------------------------------


class _SessionAccess(Protocol):
    def get_active_app(self) -> str: ...
    def set_active_app(self, app_id: str) -> None: ...
    def set_interaction(self, flow_id: str | None): ...
    def has_interaction(self) -> bool: ...
