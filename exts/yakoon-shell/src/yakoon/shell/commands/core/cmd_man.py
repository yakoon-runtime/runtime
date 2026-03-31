from typing import Protocol, cast

from yakoon.base.catalogs import (
    CommandInfo,
    CommandRegistry,
    ControllerRegistry,
)
from yakoon.base.commands import (
    Command,
    CommandScope,
    Request,
)
from yakoon.base.controllers import resolve_resource
from yakoon.base.flow import present
from yakoon.base.projection.port import ProjectorFactory


class _ControllerAccess(Protocol):
    def get_active_controller(self) -> str: ...
    def set_active_controller(self, controller_id: str) -> None: ...


class CmdMan(Command):

    key = "man"
    scope = CommandScope.GLOBAL

    async def run(self, request: Request):

        args = request.arg(0)
        if not args:
            yield self.show_index(request)
        else:
            yield self.show_manual(request)

    async def show_manual(self, request: Request):
        controller_service = self.container.get(ControllerRegistry)
        command_service = self.container.get(CommandRegistry)

        command_key = request.arg(0)
        if not command_key:
            projector = await self.create_projector()
            projection = await projector.project("no_manual_entry", command_key="")
            yield present(projection)
            return

        # privileged access: controller management
        session = self.ctx.session
        access = cast(_ControllerAccess, session)

        active_controller_id = access.get_active_controller()
        if not active_controller_id:
            active_controller_id = controller_service.shell()[0].id

        # active controller must be listed to show man pages
        if not controller_service.is_listed(active_controller_id):
            return

        # ----------------------------------------------------
        # 1) Try active controller first
        # ----------------------------------------------------
        cmd_info: CommandInfo | None = None
        owner_controller_id = active_controller_id

        for c in command_service.for_controller(active_controller_id):
            if c.key == command_key:
                cmd_info = c
                break

        # ----------------------------------------------------
        # 2) If not found: try GLOBAL commands from all controllers
        # ----------------------------------------------------
        if not cmd_info:
            global_hits: list[tuple[str, CommandInfo]] = []

            for ctrl in controller_service.all():
                if not controller_service.is_listed(ctrl.id):
                    continue
                for c in command_service.for_controller(ctrl.id):
                    if c.key == command_key and c.scope == CommandScope.GLOBAL:
                        global_hits.append((ctrl.id, c))

            if len(global_hits) == 1:
                owner_controller_id, cmd_info = global_hits[0]
            elif len(global_hits) > 1:
                raise RuntimeError(
                    f"Duplicate GLOBAL command key detected: {command_key}"
                )

        # ----------------------------------------------------
        # 3) Render or show "no entry"
        # ----------------------------------------------------
        if not cmd_info:
            projector = await self.create_projector()
            projection = await projector.project(
                "no_manual_entry", command_key=command_key
            )
            yield present(projection)
            return

        # controller has to exist - command was found before.
        controller = controller_service.get(owner_controller_id)
        if not controller:
            raise RuntimeError("Controller not found")

        resources = controller.resources
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
                key=cmd_info.key,
            )
            projector = await projector_service.create(ref, session)
            projection = await projector.project("man_page")
            yield present(projection)

        except LookupError:
            # use the own projector.
            projector = await self.create_projector()
            projection = await projector.project(
                "no_manual_entry", command_key=command_key
            )
            yield present(projection)

    async def show_index(self, request: Request):

        projector = await self.create_projector()
        controller_service = self.container.get(ControllerRegistry)
        command_service = self.container.get(CommandRegistry)

        # privileged access: controller management
        session = self.ctx.session
        access = cast(_ControllerAccess, session)

        shell = controller_service.shell()[0]
        active_controller_id = access.get_active_controller()
        mode = self.resolve_man_mode(request)

        globals_by_key: dict[str, CommandInfo] = {}

        # ----------------------------
        # Shell mode (no active or shell)
        # ----------------------------
        if not active_controller_id or active_controller_id == shell.id:
            # 1) shell commands (defined in shell controller)
            shell_commands = list(
                command_service.for_man_entries(shell.id, session, mode=mode)
            )

            # 2) global commands (defined anywhere)
            for ctrl in controller_service.all():
                if not controller_service.is_listed(ctrl.id):
                    continue
                for cmd in command_service.for_man_entries(ctrl.id, session, mode=mode):
                    if cmd.scope == CommandScope.GLOBAL:
                        globals_by_key[cmd.key] = cmd

            # merge, avoid duplicates
            merged_by_key: dict[str, CommandInfo] = {c.key: c for c in shell_commands}
            for k, v in globals_by_key.items():
                merged_by_key.setdefault(k, v)

            shell_commands = sorted(merged_by_key.values(), key=lambda c: c.key)

            controllers = sorted(
                [c for c in controller_service.listed() if c != shell],
                key=lambda c: c.id,
            )

            projection = await projector.project(
                "show_help",
                mode="shell",
                shell_commands=shell_commands,
                controllers=controllers,
            )
            yield present(projection)
            return

        # ----------------------------
        # Program mode (active != shell)
        # ----------------------------

        # 1) Collect GLOBAL commands from all controllers (system-wide available)
        for ctrl in controller_service.all():
            for cmd in command_service.for_man_entries(ctrl.id, session, mode=mode):
                if cmd.scope == CommandScope.GLOBAL:
                    globals_by_key[cmd.key] = cmd

        # 2) Collect commands from active controller that are executable in program mode
        program_by_key: dict[str, CommandInfo] = {}
        for cmd in command_service.for_man_entries(
            active_controller_id, session, mode=mode
        ):
            if cmd.scope in (CommandScope.CONTROLLER, CommandScope.GLOBAL):
                program_by_key[cmd.key] = cmd

        # 3) Merge (active controller wins on duplicates, but GLOBAL keys should be unique anyway)
        merged: dict[str, CommandInfo] = {}
        merged.update(globals_by_key)
        merged.update(program_by_key)

        commands = sorted(merged.values(), key=lambda c: c.key)
        projection = await projector.project(
            "show_help", mode="program", commands=commands
        )
        yield present(projection)

    def resolve_man_mode(self, request: Request) -> str:
        if request.has_option("internal"):
            return "internal"
        if request.has_option("all"):
            return "all"
        return "default"
