from __future__ import annotations

from abc import ABC
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, TypeVar

from yakoon.base.plugins.container import ModulePorts

if TYPE_CHECKING:
    from yakoon.base.commands import Command, CommandGroup
    from yakoon.base.runtime.sessions import Session

TComposer = TypeVar("TComposer", bound="Composer")
CommandFactory = Callable[[TComposer], "Command"]


class Composer(ABC):

    command_groups: Sequence[type[CommandGroup]]
    """Semantic command groups exported by this composer."""

    command_factories: dict[
        type[Command],
        CommandFactory,
    ]

    ports: ModulePorts

    def __init__(
        self,
        session: Session,
        command: type[Command],
    ):
        self.session = session
        self.command = command

    # ----------------------------------
    # HELPERS
    # ----------------------------------

    def port(self, cls):
        return self.ports.on_get_port(cls)

    # ----------------------------------
    # CREATE COMMAND
    # ----------------------------------

    def create_command(self) -> Command:

        factory = self.command_factories.get(self.command)
        if factory is None:
            raise RuntimeError(f"No factory registered for command: {self.command}")

        return factory(self)

    # ----------------------------------
    # BIND
    # ----------------------------------

    @classmethod
    def attach_runtime(cls, app):
        for group in cls.command_groups:
            for cmd in group.commands:
                cmd.composer = cls
                cmd.group = group
                cmd.app = app

    # ----------------------------------
    # VALIDATION
    # ----------------------------------

    @classmethod
    def validate(cls):
        for group in cls.command_groups:
            for cmd in group.commands:
                defaults = [x for x in cmd.invocations if x.default]
                if len(defaults) > 1:
                    raise RuntimeError(
                        f"Command '{cmd.key}' defines multiple default invocations."
                    )
