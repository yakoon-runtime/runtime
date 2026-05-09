from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .errors import MissingAction, UnsupportedAction
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

    anonymous = False
    subcommands: list[str] = []

    @classmethod
    def ensure_invocation(
        cls,
        tokens: list[str] | None,
    ):
        if not cls.subcommands:
            return

        if not tokens:
            raise MissingAction(
                command=cls.key,
                supported=cls.subcommands,
            )

        action = tokens[0]
        if action not in cls.subcommands:
            raise UnsupportedAction(
                command=cls.key,
                action=action,
                supported=cls.subcommands,
            )

    @abstractmethod
    def run(self, request: Request):
        raise NotImplementedError
