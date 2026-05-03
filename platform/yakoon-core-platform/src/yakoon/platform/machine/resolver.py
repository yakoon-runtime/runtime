from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from yakoon.base.application.application import Application
from yakoon.base.commands import Command
from yakoon.base.commands.types import CommandScope
from yakoon.base.controllers import Controller
from yakoon.platform.runtime import CommandNotFound


class CommandResolver:

    def __init__(self, applications: Sequence[Application]):
        self._applications = {a.id: a for a in applications}
        self._shell_app = next(a for a in applications if a.is_shell)

        self._controllers: dict[str, type[Controller]] = {}
        self._commands_by_controller: dict[str, dict[str, type[Command]]] = {}

        self._global: dict[str, type[Command]] = {}
        self._shell: dict[str, type[Command]] = {}

        self._build()

    def _build(self):

        for app in self._applications.values():
            for controller in app.controllers:

                if controller.id in self._controllers:
                    raise ValueError(f"Duplicate controller.id: {controller.id}")

                self._controllers[controller.id] = controller

                by_key = self._commands_by_controller.setdefault(controller.id, {})

                for cs in controller.commandsets:
                    for cmd in cs.commands:

                        cmd.app_id = app.id
                        cmd.controller_id = controller.id

                        if cmd.key in by_key:
                            raise ValueError(
                                f"Duplicate command key '{cmd.key}' in {controller.id}"
                            )

                        by_key[cmd.key] = cmd

                        # GLOBAL
                        if cmd.scope == CommandScope.GLOBAL:
                            if cmd.key in self._global:
                                raise ValueError(f"GLOBAL conflict: {cmd.key}")
                            self._global[cmd.key] = cmd

                        # SHELL
                        if cmd.scope == CommandScope.SHELL:
                            if cmd.key in self._shell:
                                raise ValueError(f"SHELL conflict: {cmd.key}")
                            self._shell[cmd.key] = cmd

    def resolve(
        self,
        app_id: str | None,
        command_key: str,
    ) -> tuple[Application, type[Controller], type[Command]]:

        key = command_key.strip()
        if not key:
            raise CommandNotFound(key)

        if app_id is None:
            app = self._shell_app
        else:
            app = self._applications.get(app_id)

        if not app:
            raise CommandNotFound(key)

        # 1. APP scope
        for controller in app.controllers:
            cmds = self._commands_by_controller.get(controller.id, {})
            cmd = cmds.get(key)
            if cmd and cmd.scope == CommandScope.APP:
                return app, controller, cmd

        # 2. SHELL scope
        if app.is_shell:
            cmd = self._shell.get(key)
            if cmd:
                controller = self._controllers[cmd.controller_id]
                app = self._applications[cmd.app_id]
                return app, controller, cmd

        # 3. GLOBAL scope
        cmd = self._global.get(key)
        if cmd:
            controller = self._controllers[cmd.controller_id]
            target_app = self._applications[cmd.app_id]
            return target_app, controller, cmd

        raise CommandNotFound(key)

    def globals(self) -> set[str]:
        return set(self._global.keys())


# ----------------------------------
# PORTS
# ----------------------------------


class OnMatchCommand(Protocol):
    def __call__(self, *, app_id: str, command_key: str) -> type[Command] | None: ...
