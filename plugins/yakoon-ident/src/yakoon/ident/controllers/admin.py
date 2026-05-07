from __future__ import annotations

from yakoon.base.commands import Command
from yakoon.base.controllers import Controller, ResourceReferences
from yakoon.base.naming import Namespace, NamespaceResolver
from yakoon.base.plugins.ports import OnSaveSession

from ..commands import AdminCommands, CmdGroup, CmdUser
from ..services import GroupService, UserService


class AdminController(Controller):

    id: str = "id-ident-admin"

    commandsets = (AdminCommands,)

    resources = ResourceReferences(
        package="yakoon.ident",
    )

    command_builders: dict[type[Command], str] = {
        CmdUser: "_create_user",
        CmdGroup: "_create_group",
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

    def _create_group(self):

        group_service = self.ports.on_get_port(GroupService)

        def get_group_namespace() -> Namespace:
            resolver = NamespaceResolver()
            return resolver.from_session(self.session, "group", "global")

        return CmdGroup(
            on_project=self.project,
            on_list_groups=group_service.list_groups,
            on_add_group=group_service.add_group,
            on_edit_group=group_service.edit_group,
            on_delete_group=group_service.delete_group,
            on_get_namspace=get_group_namespace,
        )
