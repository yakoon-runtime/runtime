from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .types import (
    CommandKind,
    CommandScope,
    CommandVisibility,
)

if TYPE_CHECKING:
    from .request import Request


class Command(ABC):
    """Base class for all executable commands."""

    # Public identity
    key: str

    app_id: str
    controller_id: str

    # Execution metadata
    kind: CommandKind = CommandKind.USER
    scope: CommandScope = CommandScope.APP
    visibility: CommandVisibility = CommandVisibility.NORMAL
    use_subcommands: bool = False

    @abstractmethod
    def run(self, request: Request):
        raise NotImplementedError
