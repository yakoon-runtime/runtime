from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yakoon.base.commands import Command
    from yakoon.base.controllers import Composer
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

    composers: Sequence[type[Composer]]
    """Contains the controllers of this application."""

    ports: ModulePorts

    def __init__(self):
        for composer in self.composers:
            composer.attach_runtime(self)

    def initialize(self):
        for composer in self.composers:
            composer.validate()

    def bind_ports(self, ports: ModulePorts):
        self.ports = ports
        for composer in self.composers:
            composer.ports = ports

        self.on_build(ports)

    async def start(self) -> None:
        """self.on_projection_register(
            on_register=self.ports.on_get_port(OnProjectionRegister),
        )
        self.on_manual_register(
            on_register=self.ports.on_get_port(OnManualRegister),
        )
        await self.on_start(self.ports)"""
        pass

    def create_command(
        self,
        command: type[Command],
        session: Session,
    ) -> Command:

        composer = command.composer(session, command)
        return composer.create_command()

    # ----------------------------------
    # HOOKS
    # ----------------------------------

    def on_build(self, ports: ModulePorts) -> None:  # noqa: B027
        """Hook executed after bind ports"""
        pass

    # @abstractmethod
    def on_projection_register(  # noqa: B027
        self, on_register: OnProjectionRegister
    ) -> None:
        pass

    def on_manual_register(  # noqa: B027
        self,
        on_register: OnManualRegister,
    ) -> None:
        pass

    async def on_start(self, ports: ModulePorts) -> None:  # noqa: B027
        """Hook executed after bind ports"""
        pass
