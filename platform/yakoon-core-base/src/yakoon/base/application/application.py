from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yakoon.base.commands import Command
    from yakoon.base.controllers import Controller
    from yakoon.base.plugins import ModulePorts
    from yakoon.base.runtime.sessions import Session


class Application(ABC):

    id: str = "unnamed"
    """Unique controller identifier used for command prefix resolution."""

    name: str = "unnamed"
    """Display controller name used for displaying."""

    is_shell: bool = False
    """If True, the controller acts as a shell-like environment."""

    is_listed: bool = True
    """If False, the controller is hidden from listings (e.g. man/help, UI menus)."""

    is_activatable: bool = True
    """If False, the controller cannot be activated as an interactive context."""

    controllers: Sequence[type[Controller]]
    """Contains the controllers of this application."""

    ports: ModulePorts

    def bind_ports(self, ports: ModulePorts):
        self.ports = ports
        for controller in self.controllers:
            controller.ports = ports

        self.on_build(ports)

    def on_build(self, ports: ModulePorts) -> None:  # noqa: B027
        """Hook executed after bind ports"""
        pass

    async def on_start(self, ports: ModulePorts) -> None:  # noqa: B027
        """Hook executed after bind ports"""
        pass

    async def start(self) -> None:
        await self.on_start(self.ports)

    def create_command(
        self,
        controller: type[Controller],
        command: type[Command],
        session: Session,
    ) -> Command:

        if controller not in self.controllers:
            raise RuntimeError(
                f"create_command: Invalid controller in {self.__class__}"
            )

        ctrl = controller(session, command)
        return ctrl.create_command()
