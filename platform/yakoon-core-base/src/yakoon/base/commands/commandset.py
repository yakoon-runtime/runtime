from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from yakoon.base.commands.command import Command


class CommandSet(Protocol):
    """A named collection of command classes for registration.

    A CommandSet is the unit of composition for plugins/modules: it groups commands
    (usually by feature) and exposes them to a registry.

    Attributes:
        group: Human-readable category label (used for help/man pages or UI grouping).
    """

    group: str

    @classmethod
    def commands(cls) -> Sequence[type[Command]]:
        """Return the command classes exposed by this set."""
        ...


def build_command_set(
    commands: Sequence[type[Command]],
    *,
    grp: str = "unnamed",
) -> type[CommandSet]:
    """Build an ad-hoc CommandSet from command classes.

    This is useful for tests, plugin composition, or dynamic assembly where you
    don't want to define a dedicated CommandSet type.

    Args:
        commands: Command classes to expose.
        group: Category label for display/grouping.

    Returns:
        A concrete CommandSet type.
    """

    class InlineCommandSet:
        """Inline CommandSet wrapper for dynamically provided command classes."""

        group = grp

        @staticmethod
        def commands() -> Sequence[type[Command]]:
            return commands

    return InlineCommandSet
