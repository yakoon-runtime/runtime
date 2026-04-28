from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, cast

from yakoon.base.commands import Command
from yakoon.base.commands.types import CommandKind
from yakoon.base.controllers import Controller, ResourceReferences
from yakoon.base.plugins.ports import (
    OnCheckAppListed,
    OnGetApp,
    OnGetShell,
    OnListApps,
    OnListCommandsForApp,
    OnListCommandsForManual,
    OnListListedApps,
    OnSaveSession,
)
from yakoon.shell.commands.system import (
    CmdExit,
    CmdMan,
    CmdQuit,
    CmdUse,
    CmdVersion,
    CmdWelcome,
)

from .commands.system.cmdset import ShellSystemCommands


class ShellSystemController(Controller):

    id: str = "shell-system-controller"

    commandsets = (ShellSystemCommands,)

    resources = ResourceReferences(
        package="yakoon.shell",
    )

    command_builders: dict[type[Command], str] = {
        CmdExit: "_create_exit",
        CmdVersion: "_create_version",
        CmdWelcome: "_create_welcome",
        CmdUse: "_create_use",
        CmdQuit: "_create_quit",
        CmdMan: "_create_man",
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

    def _create_quit(self):
        access = cast(_SessionAccess, self.session)
        return CmdQuit(
            on_project=self.project,
            on_set_mark=access.mark,
        )

    def _create_welcome(self):
        return CmdWelcome(on_project=self.project)

    def _create_use(self):
        access = cast(_SessionAccess, self.session)

        async def save_session():
            on_save_session = self.ports.on_get_port(OnSaveSession)
            await on_save_session(session=self.session)

        return CmdUse(
            on_project=self.project,
            on_get_app=self.ports.on_get_port(OnGetApp),
            on_list_apps=self.ports.on_get_port(OnListApps),
            on_get_active_app=access.get_active_app,
            on_set_active_app=access.set_active_app,
            on_save_session=save_session,
        )

    def _create_man(self):
        access = cast(_SessionAccess, self.session)

        def for_man(
            app_id: str, mode: str, kind_filter: CommandKind | None = None
        ) -> Sequence[type[Command]]:

            for_man_pages = self.ports.on_get_port(OnListCommandsForManual)
            return for_man_pages(
                app_id=app_id, session=self.session, mode=mode, kind_filter=kind_filter
            )

        return CmdMan(
            on_project=self.project,
            on_get_app=self.ports.on_get_port(OnGetApp),
            on_get_shell=self.ports.on_get_port(OnGetShell),
            on_get_active_app=access.get_active_app,
            on_list_apps=self.ports.on_get_port(OnListApps),
            on_list_listed_apps=self.ports.on_get_port(OnListListedApps),
            on_list_commands_for_app=self.ports.on_get_port(OnListCommandsForApp),
            on_check_app_listed=self.ports.on_get_port(OnCheckAppListed),
            on_get_commands_for_manual=for_man,
        )

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
    def mark(self, name: str): ...
