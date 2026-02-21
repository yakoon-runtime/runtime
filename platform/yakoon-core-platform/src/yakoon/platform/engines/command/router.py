from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from yakoon.base.models.command import CommandScope

if TYPE_CHECKING:
    from yakoon.base.commands.command import Command
    from yakoon.base.commands.commandset import CommandSet


class CommandDirectory:
    """
    Resolves commands by key and active controller using CommandScope.

    Responsibilities:
      - Deterministic routing
      - Scope enforcement
      - Global conflict detection
    """

    def __init__(self) -> None:
        self._routers: dict[str, CommandRouter] = {}
        self._shell_id: str | None = None

    def register(self, controller_id: str, router: CommandRouter) -> None:
        if controller_id in self._routers:
            raise ValueError(f"Duplicate controller router: {controller_id}")

        self._routers[controller_id] = router

        if router.is_shell:
            if self._shell_id is not None:
                raise ValueError(
                    f"Multiple shell controllers detected: "
                    f"{self._shell_id} and {controller_id}"
                )
            self._shell_id = controller_id

    def find(
        self,
        active_controller_id: str,
        command_key: str,
    ) -> tuple[str, Command] | None:
        """
        Resolve a command key according to CommandScope rules.

        Returns:
            (owner_controller_id, Command instance)
            or None if not found.
        """

        key = command_key.strip()

        active_router = self._routers.get(active_controller_id)
        if not active_router:
            return None

        # ----------------------------------------
        # 1) Try active controller first
        # ----------------------------------------

        cmd_type = active_router.get_type(key)
        if cmd_type:
            scope = getattr(cmd_type, "scope", CommandScope.CONTROLLER)

            if scope == CommandScope.CONTROLLER:
                return active_controller_id, cmd_type()

            if scope == CommandScope.SHELL:
                if active_router.is_shell:
                    return active_controller_id, cmd_type()

            if scope == CommandScope.GLOBAL:
                return active_controller_id, cmd_type()

        # ----------------------------------------
        # 2) Global fallback (search all routers)
        # ----------------------------------------

        global_hits: list[tuple[str, type[Command]]] = []

        for owner_id, router in self._routers.items():
            cmd_type = router.get_type(key)
            if not cmd_type:
                continue

            scope = getattr(cmd_type, "scope", CommandScope.CONTROLLER)
            if scope == CommandScope.GLOBAL:
                global_hits.append((owner_id, cmd_type))

        if len(global_hits) == 1:
            owner_id, cmd_type = global_hits[0]
            return owner_id, cmd_type()

        if len(global_hits) > 1:
            raise ValueError(f"Duplicate GLOBAL command key detected: '{key}'")

        # ----------------------------------------
        # Not found
        # ----------------------------------------

        return None

    def validate(self) -> None:
        """
        Validate global/shell scope invariants.
        Call once after all routers are registered.
        """

        global_keys: dict[str, str] = {}
        shell_keys: dict[str, str] = {}

        for controller_id, router in self._routers.items():
            for key, cmd_type in router.all_types().items():
                scope = getattr(cmd_type, "scope", CommandScope.CONTROLLER)

                if scope == CommandScope.GLOBAL:
                    if key in global_keys:
                        raise ValueError(
                            f"GLOBAL command key conflict: '{key}' "
                            f"({global_keys[key]} vs {controller_id})"
                        )
                    global_keys[key] = controller_id

                if scope == CommandScope.SHELL:
                    if controller_id != self._shell_id:
                        raise ValueError(
                            f"SHELL scoped command '{key}' must belong to "
                            f"shell controller (found in '{controller_id}')"
                        )

                    if key in shell_keys:
                        raise ValueError(f"Duplicate SHELL command key: '{key}'")
                    shell_keys[key] = controller_id


class CommandRouter:

    def __init__(
        self, controller_id: str, is_shell: bool, is_listed: bool, is_activatable: bool
    ):
        self.controller_id = controller_id
        self.is_shell = is_shell
        self.is_listed = is_listed
        self.is_activatable = is_activatable
        self._by_key: dict[str, type[Command]] = {}

    def register(self, owner_id: str, commandsets: Sequence[type[CommandSet]]) -> None:
        for cs_type in commandsets:
            for cmd_type in cs_type.commands():
                key = cmd_type.key
                if key in self._by_key:
                    raise ValueError(
                        f"Duplicate command key in controller '{owner_id}': {key}"
                    )
                self._by_key[key] = cmd_type

    def get_type(self, key: str) -> type[Command] | None:
        return self._by_key.get(key)

    def all_types(self) -> dict[str, type[Command]]:
        return self._by_key

    def instantiate(self, key: str) -> Command | None:
        t = self.get_type(key)
        return t() if t else None
