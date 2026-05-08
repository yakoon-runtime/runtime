from __future__ import annotations

from yakoon.base.commands import Command
from yakoon.base.controllers import Controller, ResourceReferences
from yakoon.base.naming import Key, NamespaceResolver
from yakoon.base.plugins.models import AuthResult
from yakoon.base.plugins.ports import OnAuthenticate, OnSaveSession
from yakoon.ident.services import IdentityNamespaces
from yakoon.platform.capabilities.permission import PermissionSet

from ..commands import AuthCommands, CmdSu, CmdWhoAmI
from ..services import PermissionResolver


class AuthController(Controller):

    id: str = "id-ident-auth"

    commandsets = (AuthCommands,)

    resources = ResourceReferences(
        package="yakoon.ident",
    )

    command_builders: dict[type[Command], str] = {
        CmdWhoAmI: "_create_whoami",
        CmdSu: "_create_su",
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
    # AUTHENTICATE
    # ----------------------------------

    async def _authenticate(self, username: str, secret: str) -> AuthResult:
        resolver = NamespaceResolver()
        namespace = resolver.from_session(self.session, "user", "global")

        on_authenticate = self.ports.on_get_port(OnAuthenticate)
        return await on_authenticate(
            namespace=namespace,
            username=username,
            secret=secret,
        )

    # ----------------------------------
    # SESSION HANDLING
    # ----------------------------------

    async def _save_session(self):
        on_save_session = self.ports.on_get_port(OnSaveSession)
        await on_save_session(session=self.session)

    # ----------------------------------
    # APPLY PERMISSIONS
    # ----------------------------------

    def _apply_permissions(self, permissions: PermissionSet):
        self.session.set_permissions(permissions)

    # ----------------------------------
    # FACTORY
    # ----------------------------------

    def _create_su(self):

        async def resolve_permission(user_key: Key):
            resolver = self.ports.on_get_port(PermissionResolver)
            permissions = await resolver.resolve_user_permissions(
                grant_namespace=self.namespaces.permgrant_namespace(),
                membership_namespace=self.namespaces.membership_namespace(),
                user_key=user_key,
            )
            self._apply_permissions(permissions)

        return CmdSu(
            on_project=self.project,
            on_set_identity=self.session.set_identity,
            on_store_session=self._save_session,
            on_authenticate=self._authenticate,
            on_apply_permissions=resolve_permission,
        )

    def _create_whoami(self):

        def get_user() -> str:
            return str(self.session.get_identity() or "")

        return CmdWhoAmI(
            on_project=self.project,
            on_get_user=get_user,
        )
