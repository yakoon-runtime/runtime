from __future__ import annotations

from typing import Any, Protocol, cast

from yakoon.base.commands import Command
from yakoon.base.commands.types import CommandKind
from yakoon.base.controllers import Controller, ResourceReferences
from yakoon.base.controllers.resolver import resolve_resource
from yakoon.base.plugins.ports import OnAuthorize, OnProject, OnSaveSession
from yakoon.base.resources.resource import ResourceRef
from yakoon.base.sources import OnDataSource

from ..commands.system import (
    CmdExit,
    CmdMan,
    CmdQuit,
    CmdUse,
    CmdVersion,
    CmdWelcome,
    SystemCommands,
)
from ..services import CommandManService


class SystemController(Controller):

    id: str = "shell-system-controller"

    commandsets = (SystemCommands,)

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
            on_source=self.ports.on_get_port(OnDataSource),
            on_project=self.project,
            on_get_active_app=access.get_active_app,
            on_set_active_app=access.set_active_app,
            on_save_session=save_session,
        )

    def _create_man(self):
        access = cast(_SessionAccess, self.session)
        manual_service = CommandManService(
            on_source=self.ports.on_get_port(OnDataSource),
            on_has_permission=self.ports.on_get_port(OnAuthorize),
        )

        async def list_commands(
            app_id: str, mode: str, kind: CommandKind | None = None
        ) -> list[dict[str, Any]]:
            return await manual_service.get_entries(
                app_id=app_id, session=self.session, mode=mode, kind=kind
            )

        def _resolve_manual_resource(resources, name):
            path = resolve_resource(
                i18n_root=resources["contracts"],
                lang=self.session.lang,
                cmd_key=self.command.key,
            )
            return ResourceRef(resources["package"], path).child(name)

        async def project_manual(resources: dict, name: str, state: dict | None = None):
            resource = _resolve_manual_resource(resources=resources, name=name)
            on_project = self.ports.on_get_port(OnProject)
            return await on_project(resource=resource, state=state)

        return CmdMan(
            on_project=self.project,
            on_project_manual=project_manual,
            on_list_manual=list_commands,
            on_source=self.ports.on_get_port(OnDataSource),
            on_get_active_app=access.get_active_app,
        )

    def _create_exit(self):
        access = cast(_SessionAccess, self.session)

        async def save_session():
            on_save_session = self.ports.on_get_port(OnSaveSession)
            await on_save_session(session=self.session)

        return CmdExit(
            on_source=self.ports.on_get_port(OnDataSource),
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
