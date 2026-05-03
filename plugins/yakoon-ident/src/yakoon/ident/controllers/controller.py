from __future__ import annotations

from typing import Protocol, cast

from yakoon.base.commands import Command
from yakoon.base.controllers import Controller, ResourceReferences
from yakoon.base.naming import Key, NamespaceResolver
from yakoon.base.plugins.models import AuthResult
from yakoon.base.plugins.ports import OnAuthenticate

from ..commands import BaseCommands, CmdSu, CmdWhoAmI


class BaseController(Controller):
    """Authentication controller.

    Provides:
        - System-level authentication commands
        - Templates under yakoon.auth:core
    """

    id: str = "id-base"

    commandsets = (BaseCommands,)

    resources = ResourceReferences(
        package="yakoon.ident",
    )

    command_builders: dict[type[Command], str] = {
        CmdWhoAmI: "_create_whoami",
        CmdSu: "_create_su",
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
    # AUTHENTICATE
    # ----------------------------------

    async def _authenticate(self, username: str, secret: str) -> AuthResult:
        resolver = NamespaceResolver()
        namespace = resolver.from_session(self.session, "account", "develop")

        on_authenticate = self.ports.on_get_port(OnAuthenticate)
        return await on_authenticate(
            namespace=namespace,
            username=username,
            secret=secret,
        )

    # ----------------------------------
    # FACTORY
    # ----------------------------------

    def _create_su(self):
        access = cast(_SessionAccess, self.session)

        return CmdSu(
            on_project=self.project,
            on_set_identity=access.set_identity,
            on_authenticate=self._authenticate,
        )

    def _create_whoami(self):
        access = cast(_SessionAccess, self.session)

        return CmdWhoAmI(
            on_project=self.project,
            on_get_user=access.get_username,
        )


# ----------------------------------
# SESSION ACCESS
# ----------------------------------


class _SessionAccess(Protocol):
    def get_username(self) -> str: ...
    def set_identity(self, key: Key, user_name: str): ...
