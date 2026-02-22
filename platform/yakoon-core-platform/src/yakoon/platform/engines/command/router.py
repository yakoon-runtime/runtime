from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from yakoon.base import ports
from yakoon.base.directories.service import ServiceDirectory

if TYPE_CHECKING:
    from yakoon.base.commands.command import Command
    from yakoon.base.commands.commandset import CommandSet


class CommandDirectory:
    """
    Engine-only command type registry.

    Holds real command types per controller and materializes Command instances.
    Resolve semantics (scope/order) live in CommandCatalogService (CommandInfo-only).

    Internal structure:
        controller_id -> (command_key -> CommandType)
    """

    def __init__(self, services: ServiceDirectory) -> None:
        self._services = services
        self._types: dict[str, dict[str, type[Command]]] = {}

    # ---------------------------------------------------------------------
    # Registration
    # ---------------------------------------------------------------------

    def register(
        self,
        controller_id: str,
        commandsets: Sequence[type[CommandSet]],
    ) -> None:
        """
        Register all command types for a controller.
        No metadata, no scope logic — only type registration.

        Raises:
            ValueError on duplicate command keys within the controller.
        """
        by_key = self._types.setdefault(controller_id, {})

        for cs_type in commandsets:
            for cmd_type in cs_type.commands():
                key = cmd_type.key
                if key in by_key:
                    raise ValueError(
                        f"Duplicate command key in controller '{controller_id}': '{key}'"
                    )
                by_key[key] = cmd_type

    def all_types_for(self, controller_id: str) -> Mapping[str, type[Command]]:
        return self._types.get(controller_id, {})

    def get_type(self, controller_id: str, key: str) -> type[Command] | None:
        return self._types.get(controller_id, {}).get(key)

    # ---------------------------------------------------------------------
    # Resolve + materialize
    # ---------------------------------------------------------------------

    def find(self, controller_id: str, command_key: str) -> tuple[str, Command] | None:
        """
        Resolve a command within a controller context and materialize it.

        NOTE:
            The input controller_id is the *resolve context*.
            The returned owner_id is the *defining controller* of the resolved command
            (can differ due to GLOBAL/SHELL scope rules handled by CommandCatalogService).
        """
        key = command_key.strip()
        if not key:
            return None

        catalog = self._services.get(ports.CommandCatalogService)

        # resolve_info() decides WHICH defining controller owns that command (CommandInfo.controller_id)
        ci = catalog.resolve_info(controller_id, key)
        if not ci:
            return None

        owner_id = ci.controller_id
        cmd_type = self.get_type(owner_id, ci.key)
        if not cmd_type:
            # Catalog says it exists, but we have no type -> composition mismatch
            return None

        return owner_id, cmd_type()

    # ---------------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------------

    def validate(self) -> None:
        """
        Validate registry-level integrity + cross-check against CommandCatalogService.

        Ensures:
          - every CommandInfo has a corresponding real command type
          - optionally, no real type exists without a CommandInfo (prevents "ghost commands")
        """
        catalog = self._services.get(ports.CommandCatalogService)

        missing: list[str] = []
        for ci in catalog.all():
            if ci.controller_id not in self._types:
                missing.append(f"{ci.controller_id}:{ci.key} (controller missing)")
                continue
            if ci.key not in self._types[ci.controller_id]:
                missing.append(f"{ci.controller_id}:{ci.key} (type missing)")

        if missing:
            raise ValueError(
                "CommandCatalog/CommandDirectory mismatch. Missing command types:\n"
                + "\n".join(missing)
            )

        # Optional reverse check: types without infos
        info_keys = {(ci.controller_id, ci.key) for ci in catalog.all()}
        extra: list[str] = []
        for owner_id, by_key in self._types.items():
            for key in by_key.keys():
                if (owner_id, key) not in info_keys:
                    extra.append(f"{owner_id}:{key}")

        if extra:
            raise ValueError(
                "CommandDirectory contains commands not present in CommandCatalog:\n"
                + "\n".join(extra)
            )
