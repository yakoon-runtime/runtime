from __future__ import annotations

from yakoon.base.commands import Command
from yakoon.base.controllers import Controller, ResourceReferences
from yakoon.base.naming import Namespace, NamespaceResolver
from yakoon.base.plugins.ports import OnSaveSession

from ..commands import CmdUser, UserCommands
from ..services import UserService


class UserAdminController(Controller):

    id: str = "id-user"

    commandsets = (UserCommands,)

    resources = ResourceReferences(
        package="yakoon.ident",
    )

    command_builders: dict[type[Command], str] = {
        CmdUser: "_create_user",
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

        user_service = self.ports.on_get_port(UserService)

        def get_user_namespace() -> Namespace:
            resolver = NamespaceResolver()
            return resolver.from_session(self.session, "user", "global")

        return CmdUser(
            on_project=self.project,
            on_list_users=user_service.list_users,
            on_add_user=user_service.add_user,
            on_edit_user=user_service.edit_user,
            on_delete_user=user_service.delete_user,
            on_get_namspace=get_user_namespace,
        )
