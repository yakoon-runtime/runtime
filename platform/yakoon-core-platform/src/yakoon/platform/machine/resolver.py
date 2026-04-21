from __future__ import annotations

from yakoon.base.catalogs import CommandQuery
from yakoon.base.commands import Command
from yakoon.base.controllers import Controller


class CommandResolver:

    def __init__(self, query: CommandQuery):
        self._query = query
        self._controllers: dict[str, type[Controller]] = {}
        self._types: dict[str, dict[str, type[Command]]] = {}

    def register(
        self,
        controller: type[Controller],
    ) -> None:

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
        ci = self._query.for_context(app_id, key)
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
