from __future__ import annotations

from yakoon.base.commands import Command
from yakoon.base.controllers import Composer, ResourceReferences
from yakoon.base.plugins.ports import OnSaveSession
from yakoon.ident.models import Group, User

from ..commands import (
    AdminCommands,
    CmdGroup,
    CmdMembership,
    CmdPermissionGrant,
    CmdUser,
)
from ..services import (
    GroupService,
    IdentityNamespaces,
    MembershipService,
    PermissionGrantService,
    UserService,
)


class AdminComposer(Composer):

    command_groups = (AdminCommands,)

    resources = ResourceReferences(
        package="yakoon.ident",
    )

    command_builders: dict[type[Command], str] = {
        CmdUser: "_create_user",
        CmdGroup: "_create_group",
        CmdMembership: "_create_membership",
        CmdPermissionGrant: "create_permgrant",
    }

    namespaces = IdentityNamespaces()

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

        return CmdUser(
            on_project=self.project,
            on_list_users=user_service.list_users,
            on_add_user=user_service.add_user,
            on_edit_user=user_service.edit_user,
            on_delete_user=user_service.delete_user,
            on_get_namspace=self.namespaces.user_namespace,
        )

    def _create_group(self):

        group_service = self.ports.on_get_port(GroupService)

        return CmdGroup(
            on_project=self.project,
            on_list_groups=group_service.list_groups,
            on_add_group=group_service.add_group,
            on_edit_group=group_service.edit_group,
            on_delete_group=group_service.delete_group,
            on_get_namspace=self.namespaces.group_namespace,
        )

    def _create_membership(self):

        user_service = self.ports.on_get_port(UserService)
        group_service = self.ports.on_get_port(GroupService)
        membership_service = self.ports.on_get_port(MembershipService)

        async def get_user_by_name(name: str) -> User | None:
            return await user_service.get_by_username(
                namespace=self.namespaces.user_namespace(),
                username=name,
            )

        async def get_group_by_name(name: str) -> Group | None:
            return await group_service.get_by_name(
                namespace=self.namespaces.group_namespace(),
                name=name,
            )

        return CmdMembership(
            on_project=self.project,
            on_list_memberships=membership_service.list_memberships,
            on_list_user_memberships=membership_service.list_user_memberships,
            on_list_group_memberships=membership_service.list_group_memberships,
            on_add_membership=membership_service.add_membership,
            on_remove_membership=membership_service.remove_membership,
            on_get_user_by_name=get_user_by_name,
            on_get_group_by_name=get_group_by_name,
            on_get_namespace=self.namespaces.membership_namespace,
        )

    def create_permgrant(self):

        user_service = self.ports.on_get_port(UserService)
        group_service = self.ports.on_get_port(GroupService)
        permgrant_service = self.ports.on_get_port(PermissionGrantService)

        async def get_user_by_name(name: str) -> User | None:
            return await user_service.get_by_username(
                namespace=(self.namespaces.user_namespace()),
                username=name,
            )

        async def get_group_by_name(name: str) -> Group | None:
            return await group_service.get_by_name(
                namespace=(self.namespaces.group_namespace()),
                name=name,
            )

        return CmdPermissionGrant(
            on_project=self.project,
            on_list_grants=permgrant_service.list_grants,
            on_list_subject_grants=permgrant_service.list_subject_grants,
            on_list_permission_grants=permgrant_service.list_permission_grants,
            on_add_grant=permgrant_service.add_grant,
            on_remove_grant=permgrant_service.remove_grant,
            on_get_user_by_name=get_user_by_name,
            on_get_group_by_name=get_group_by_name,
            on_get_namespace=self.namespaces.permgrant_namespace,
        )
