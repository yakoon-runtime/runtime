from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from typing import Protocol

from yakoon.base.commands import Command
from yakoon.base.controllers import Controller, resolve_resource
from yakoon.base.plugins import ModuleImport
from yakoon.base.projection import Projection
from yakoon.base.resources.resource import ResourceRef


class Application(ABC):

    id: str = "unnamed"
    """Unique controller identifier used for command prefix resolution."""

    is_shell: bool = False
    """If True, the controller acts as a shell-like environment."""

    is_listed: bool = True
    """If False, the controller is hidden from listings (e.g. man/help, UI menus)."""

    is_activatable: bool = True
    """If False, the controller cannot be activated as an interactive context."""

    controllers: Sequence[type[Controller]]
    """Contains the controllers of this application."""

    def __init__(self, platform_ports: ModuleImport):
        self.on_project = platform_ports.on_project

    def create_command(
        self,
        controller: type[Controller],
        command: type[Command],
        lang: str,
    ) -> Command:

        if controller not in self.controllers:
            raise RuntimeError(
                f"create_command: Invalid controller in {self.__class__}"
            )

        async def project(name: str, state: dict | None = None) -> Projection:
            path = resolve_resource(
                i18n_root=controller.resources.contracts, lang=lang, cmd_key=command.key
            )
            resource = ResourceRef(controller.resources.package, path).child(name)
            return await self.on_project(resource=resource, state=state)

        command_inst = command()
        command_inst.on_project = project
        return command_inst


# ----------------------------------
# PORTS
# ----------------------------------


class OnProject(Protocol):
    async def __call__(self, *, name: str, state: dict | None = None) -> Projection: ...
