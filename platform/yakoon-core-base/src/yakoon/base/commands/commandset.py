from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .command import Command


class CommandSet(Protocol):
    """A named collection of command classes for registration.

    A CommandSet is the unit of composition for plugins/modules: it groups commands
    (usually by feature) and exposes them to a registry.
    """

    group: str
    """Human-readable category label (used for help/man pages or UI grouping)."""

    commands: Sequence[type[Command]]
    """Return the command classes exposed by this set."""
