from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from yakoon.base import ports
from yakoon.base.directories.service import ServiceDirectory

if TYPE_CHECKING:
    from yakoon.base.commands.command import Command
    from yakoon.base.commands.commandset import CommandSet


class CommandDirectory:
    """
    Engine-only.
    Holds real command types per controller and materializes Command instances.

    Uses CommandCatalogService for resolve ordering (CommandInfo only).
    """

    def __init__(self, services: ServiceDirectory) -> None:
        self._services = services
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

    def find(self, active_controller_id: str, key: str) -> tuple[str, Command] | None:
        catalog = self._services.get(ports.CommandCatalogService)

        ci = catalog.resolve_info(active_controller_id, key)
        if not ci:
            return None

        router = self._routers.get(ci.controller_id)
        if not router:
            return None

        cmd_type = router.get_type(ci.key)
        if not cmd_type:
            return None

        return ci.controller_id, cmd_type()

    def validate(self) -> None:
        """
        Validate router-level invariants + cross-check against CommandCatalogService.

        Ensures:
        - at most one shell controller
        - for every CommandInfo there exists a real command type in the router
        - (optional) no real command exists without a CommandInfo entry
        """
        # 1) only one shell controller
        shell_ids = [cid for cid, r in self._routers.items() if r.is_shell]
        if len(shell_ids) > 1:
            raise ValueError(f"Multiple shell controllers detected: {shell_ids}")

        # 2) cross-check CommandInfo -> real command type
        catalog = self._services.get(ports.CommandCatalogService)
        # ensure it's built; either call build() here or require compose to do it
        # I'd rather be strict:
        # catalog.build()  # if you prefer validate() to be self-sufficient

        missing: list[str] = []
        for ci in catalog.all():  # should be stable list of CommandInfo
            router = self._routers.get(ci.controller_id)
            if not router:
                missing.append(f"{ci.controller_id}:{ci.key} (router missing)")
                continue
            if not router.get_type(ci.key):
                missing.append(f"{ci.controller_id}:{ci.key} (command type missing)")

        if missing:
            raise ValueError(
                "CommandCatalog/CommandDirectory mismatch. Missing command types:\n"
                + "\n".join(missing)
            )

        # 3) OPTIONAL: real command types must also exist as CommandInfo
        info_keys = {(ci.controller_id, ci.key) for ci in catalog.all()}
        extra: list[str] = []
        for owner_id, router in self._routers.items():
            for key in router.all_types().keys():
                if (owner_id, key) not in info_keys:
                    extra.append(f"{owner_id}:{key}")

        if extra:
            raise ValueError(
                "CommandDirectory contains commands not present in CommandCatalog:\n"
                + "\n".join(extra)
            )


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
