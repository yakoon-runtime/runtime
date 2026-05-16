from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .command import Command


class CommandGroup(Protocol):
    """A semantic grouping of related commands.

    Command groups are used for runtime discovery, navigation,
    help systems, and UI organization.

    Groups do not control command composition, execution,
    or resource resolution.
    """

    group: str
    """Semantic category identifier used for grouping and discovery."""

    commands: Sequence[type[Command]]
    """Commands belonging to this semantic group."""
