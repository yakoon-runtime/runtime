from __future__ import annotations

from yakoon.base.commands import Command
from yakoon.base.controllers import Controller, ResourceReferences
from yakoon.base.plugins.ports import OnSaveSession

from ..commands import CmdUsers, UserCommands


class UserAdminController(Controller):

    id: str = "id-user"

    commandsets = (UserCommands,)

    resources = ResourceReferences(
        package="yakoon.ident",
    )

    command_builders: dict[type[Command], str] = {
        CmdUsers: "_create_user",
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
    # SESSION HANDLING
    # ----------------------------------

    async def _save_session(self):
        on_save_session = self.ports.on_get_port(OnSaveSession)
        await on_save_session(session=self.session)

    # ----------------------------------
    # FACTORY
    # ----------------------------------

    def _create_user(self):

        return CmdUsers(
            on_project=self.project,
        )
