from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models.command_info import CommandInfo


class CommandCatalog:

    def __init__(self, commands: Iterable[CommandInfo]):
        self._commands: tuple[CommandInfo, ...] = tuple(commands)

    def all(self) -> tuple[CommandInfo, ...]:
        return self._commands
