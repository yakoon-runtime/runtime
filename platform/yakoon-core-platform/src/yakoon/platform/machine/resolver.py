from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from yakoon.base.application import Application
from yakoon.base.commands import Command
from yakoon.base.controllers import Controller


class CommandResolver:

    def __init__(
        self,
        on_match_command: OnMatchCommand,
        on_get_context: OnGetContext,
    ):
        self.on_match_command = on_match_command
        self.on_get_context = on_get_context

        self._controllers: dict[str, type[Controller]] = {}
        self._types: dict[str, dict[str, type[Command]]] = {}
        self._build()

    def _build(self) -> None:

        for app in self.on_get_context():
            for controller in app.controllers:

                if controller.id in self._controllers:
                    raise ValueError(
                        f"Duplicate controller.id in controllers: '{controller.id}'"
                    )

                self._controllers[controller.id] = controller

                by_key = self._types.setdefault(controller.id, {})
                for cmd_set in controller.commandsets:
                    for cmd_type in cmd_set.commands:
                        key = cmd_type.key
                        if key in by_key:
                            raise ValueError(
                                f"Duplicate command key in controller '{controller.id}': '{key}'"
                            )
                        by_key[key] = cmd_type

    def resolve(
        self,
        app_id: str,
        command_key: str,
    ) -> tuple[str, type[Controller], type[Command]] | None:

        key = command_key.strip()
        if not key:
            return None

        matches: list[tuple[str, type[Controller], type[Command]]] = []
        ci = self.on_match_command(app_id=app_id, command_key=key)
        if not ci:
            return None

        app_id = ci.app_id
        controller_id = ci.controller_id

        # find command
        cmd_type = self._types.get(controller_id, {}).get(ci.key)
        if not cmd_type:
            return None

        # find controller.
        controller_type = next(
            (self._controllers[k] for k in self._controllers if k == controller_id),
            None,
        )
        if not controller_type:
            return None

        matches.append((app_id, controller_type, cmd_type))
        if not matches:
            return None

        if len(matches) == 1:
            return matches[0]

        owners = ", ".join(f"{app_id}:{c.id}:{cmd.key}" for app_id, c, cmd in matches)
        raise ValueError(f"Ambiguous command '{command_key}' → {owners}")


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetContext(Protocol):
    def __call__(self) -> Sequence[Application]: ...


class OnMatchCommand(Protocol):
    def __call__(self, *, app_id: str, command_key: str) -> type[Command] | None: ...
