from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from yakoon.base.application.application import Application
from yakoon.base.commands import Command, CommandScope
from yakoon.base.controllers import Controller
from yakoon.platform.capabilities.permission import Permission
from yakoon.platform.runtime import CommandNotFound, PermissionDenied
from yakoon.platform.runtime.sessions import Session


class InvocationResolver:

    def __init__(
        self,
        on_authorize: OnAuthorize,
        on_suggest: OnSuggest,
        applications: Sequence[Application],
    ):
        self.on_authorize = on_authorize
        self.on_suggest = on_suggest
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
        tokens: list[str] | None,
        session: Session,
    ) -> tuple[Application, type[Controller], type[Command]]:

        choices = []
        key = command_key.strip()
        if not key:
            raise CommandNotFound(key)

        if app_id is None:
            app = self._shell_app
        else:
            app = self._applications.get(app_id)

        if not app:
            raise CommandNotFound(key)

        # ----------------
        # 1. APP scope ---
        # ----------------

        for controller in app.controllers:
            cmds = self._commands_by_controller.get(controller.id, {})
            choices.extend(
                [
                    c.key
                    for c in cmds.values()
                    if c.scope in (CommandScope.APP, CommandScope.SHELL)
                ]
            )
            cmd = cmds.get(key)
            #!Command in own app & all own commands with SHELL Scope.
            if cmd and cmd.scope in (CommandScope.APP, CommandScope.SHELL):
                self._ensure_invocation(session, cmd, tokens)
                return app, controller, cmd

        # -------------------------------------
        # 2. SHELL scope (in case of shell) ---
        # -------------------------------------

        if app.is_shell:
            cmd = self._shell.get(key)
            choices.extend([c for c in self._shell.keys()])
            if cmd:
                controller = self._controllers[cmd.controller_id]
                app = self._applications[cmd.app_id]
                self._ensure_invocation(session, cmd, tokens)
                return app, controller, cmd

        # -------------------
        # 3. GLOBAL scope ---
        # -------------------

        cmd = self._global.get(key)
        choices.extend([c for c in self._global.keys()])
        if cmd:
            controller = self._controllers[cmd.controller_id]
            target_app = self._applications[cmd.app_id]
            self._ensure_invocation(session, cmd, tokens)
            return target_app, controller, cmd

        # -----------------
        # 4. SUGGESTION ---
        # -----------------

        suggestions = self.on_suggest(value=key, choices=choices, limit=1)
        raise CommandNotFound(command=key, suggestions=suggestions)

    def globals(self) -> set[str]:
        return set(self._global.keys())

    # ----------------------------------
    # INTERNALS
    # ----------------------------------

    def _ensure_invocation(
        self, session: Session, command_type: type[Command], tokens: list[str] | None
    ):
        command_type.ensure_invocation(tokens=tokens)
        if command_type.anonymous:
            return

        action = tokens[0] if tokens else None
        fq = Permission.fq_key(command_type.app_id, command_type.key, action)
        if not self.on_authorize(session=session, perm_key=fq):
            raise PermissionDenied()


# ----------------------------------
# PORTS
# ----------------------------------


class OnAuthorize(Protocol):
    def __call__(self, *, session, perm_key: str) -> bool: ...


class OnSuggest(Protocol):
    def __call__(
        self,
        *,
        value: str,
        choices: list[str],
        limit: int = 3,
        cutoff: float = 0.5,
    ) -> list[str]: ...
