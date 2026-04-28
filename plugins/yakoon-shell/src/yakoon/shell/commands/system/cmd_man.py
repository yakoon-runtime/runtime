from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from yakoon.base.application.application import Application
from yakoon.base.commands import (
    Command,
    CommandScope,
    Request,
)
from yakoon.base.commands.ports import OnProjectCmd
from yakoon.base.commands.types import CommandKind
from yakoon.base.flow import out


class CmdMan(Command):

    key = "man"
    scope = CommandScope.GLOBAL

    def __init__(
        self,
        on_project: OnProjectCmd,
        on_get_app: OnGetApp,
        on_get_active_app: OnGetActiveApp,
        on_list_apps: OnListApps,
        on_get_shell: OnGetShell,
        on_check_app_listed: OnCheckAppListed,
        on_list_listed_apps: OnListListedApps,
        on_list_commands_for_app: OnListCommandsForApp,
        on_get_commands_for_manual: OnListCommandsForManual,
    ):
        self.on_project = on_project
        self.on_get_app = on_get_app
        self.on_get_active_app = on_get_active_app
        self.on_list_apps = on_list_apps
        self.on_get_shell = on_get_shell
        self.on_check_app_listed = on_check_app_listed
        self.on_list_listed_apps = on_list_listed_apps
        self.on_list_commands_for_app = on_list_commands_for_app
        self.on_get_commands_for_manual = on_get_commands_for_manual

    async def run(self, request: Request):

        args = request.arg(0)
        if not args:
            yield self.show_index(request)
        else:
            yield self.show_manual(request)

    async def show_manual(self, request: Request):

        command_key = request.arg(0)
        if not command_key:
            projection = await self.on_project(
                name="error.sam",
                state={
                    "command_key": "",
                },
            )
            yield out(projection)
            return

        # privileged access: controller management

        active_app_id = self.on_get_active_app()
        if not active_app_id:
            active_app_id = self.on_get_shell().id

        # active controller must be listed to show man pages
        if not self.on_check_app_listed(app_id=active_app_id):
            return

        # ----------------------------------------------------
        # 1) Try active app first
        # ----------------------------------------------------
        command: type[Command] | None = None
        owner_app_id = active_app_id

        for c in self.on_list_commands_for_app(app_id=active_app_id):
            if c.key == command_key:
                command = c
                break

        # ----------------------------------------------------
        # 2) If not found: try GLOBAL commands from all apps
        # ----------------------------------------------------
        if not command:
            global_hits: list[tuple[str, type[Command]]] = []

            for ctrl in self.on_list_apps():
                if not self.on_check_app_listed(app_id=ctrl.id):
                    continue
                for c in self.on_list_commands_for_app(app_id=ctrl.id):
                    if c.key == command_key and c.scope == CommandScope.GLOBAL:
                        global_hits.append((ctrl.id, c))

            if len(global_hits) == 1:
                owner_app_id, command = global_hits[0]
            elif len(global_hits) > 1:
                raise RuntimeError(
                    f"Duplicate GLOBAL command key detected: {command_key}"
                )

        # ----------------------------------------------------
        # 3) Render or show "no entry"
        # ----------------------------------------------------
        if not command:
            projection = await self.on_project(
                name="error.sam",
                state={
                    "command_key": command_key,
                },
            )
            yield out(projection)
            return

        # controller has to exist - command was found before.
        app = self.on_get_app(app_id=owner_app_id)
        if not app:
            raise RuntimeError("Controller not found")

        # TODO
        resources = app.resources
        if not resources:
            raise RuntimeError("Controller has no ResourceReferences")
        if not resources.package:
            raise RuntimeError("ResourceReferences has no package")

        projector_service = self.container.get(ProjectorFactory)

        try:
            ref = resolve_resource(
                resources,
                i18n_root=resources.man,
                lang=session.lang,
                cmd_key=command.key,
            )
            projector = await projector_service.create(ref, session)
            projection = await projector.project("details")
            yield out(projection)

        except LookupError:
            # use the own projector.
            projection = await self.on_project(
                name="no_manual_entry.sam",
                state={"command_key": command_key},
            )
            yield out(projection)

    async def show_index(self, request: Request):

        shell = self.on_get_shell()
        active_app_id = self.on_get_active_app()
        mode = self.resolve_man_mode(request)

        globals_by_key: dict[str, type[Command]] = {}

        # ----------------------------
        # Shell mode (no active or shell)
        # ----------------------------
        if not active_app_id or active_app_id == shell.id:
            # 1) shell commands (defined in shell controller)
            shell_commands = list(
                self.on_get_commands_for_manual(app_id=shell.id, mode=mode)
            )

            # 2) global commands (defined anywhere)
            for app in self.on_list_apps():
                if not self.on_check_app_listed(app_id=app.id):
                    continue
                for cmd in self.on_get_commands_for_manual(app_id=app.id, mode=mode):
                    if cmd.scope == CommandScope.GLOBAL:
                        globals_by_key[cmd.key] = cmd

            # merge, avoid duplicates
            merged_by_key: dict[str, type[Command]] = {c.key: c for c in shell_commands}
            for k, v in globals_by_key.items():
                merged_by_key.setdefault(k, v)

            shell_commands = sorted(merged_by_key.values(), key=lambda c: c.key)

            apps = sorted(
                [c for c in self.on_list_listed_apps() if c != shell],
                key=lambda c: c.id,
            )

            projection = await self.on_project(
                name="overview.sam",
                state={
                    "mode": "shell",
                    "shell_commands": shell_commands,
                    "apps": apps,
                },
            )
            yield out(projection)
            return

        # ----------------------------
        # Program mode (active != shell)
        # ----------------------------

        # 1) Collect GLOBAL commands from all app (system-wide available)
        for app in self.on_list_apps():
            for cmd in self.on_get_commands_for_manual(app_id=app.id, mode=mode):
                if cmd.scope == CommandScope.GLOBAL:
                    globals_by_key[cmd.key] = cmd

        # 2) Collect commands from active app that are executable in program mode
        program_by_key: dict[str, type[Command]] = {}
        for cmd in self.on_get_commands_for_manual(app_id=active_app_id, mode=mode):
            if cmd.scope in (CommandScope.APP, CommandScope.GLOBAL):
                program_by_key[cmd.key] = cmd

        # 3) Merge (active app wins on duplicates, but GLOBAL keys should be unique anyway)
        merged: dict[str, type[Command]] = {}
        merged.update(globals_by_key)
        merged.update(program_by_key)

        commands = sorted(merged.values(), key=lambda c: c.key)
        projection = await self.on_project(
            name="show_help.sam",
            state={
                "mode": "program",
                "commands": commands,
            },
        )
        yield out(projection)

    def resolve_man_mode(self, request: Request) -> str:
        if request.has_option("internal"):
            return "internal"
        if request.has_option("all"):
            return "all"
        return "default"


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetActiveApp(Protocol):
    def __call__(self) -> str: ...


class OnGetApp(Protocol):
    def __call__(self, *, app_id: str) -> Application | None: ...


class OnListApps(Protocol):
    def __call__(self) -> Sequence[Application]: ...


class OnListListedApps(Protocol):
    def __call__(self) -> Sequence[Application]: ...


class OnGetShell(Protocol):
    def __call__(self) -> Application: ...


class OnCheckAppListed(Protocol):
    def __call__(self, *, app_id: str) -> bool: ...


class OnListCommandsForApp(Protocol):
    def __call__(self, *, app_id: str) -> Sequence[type[Command]]: ...


class OnListCommandsForManual(Protocol):
    def __call__(
        self,
        *,
        app_id: str,
        mode: str,
        kind_filter: CommandKind | None = None,
    ) -> Sequence[type[Command]]: ...
