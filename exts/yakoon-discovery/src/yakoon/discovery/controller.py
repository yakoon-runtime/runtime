from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from yakoon.base.controllers.base import BaseController
from yakoon.base.resources.reference import ResourceReferences
from yakoon.discovery.commands.cmdset import DiscoveryLookupCommands

if TYPE_CHECKING:
    from yakoon.base.commands.commandset import CommandSet


class DiscoveryController(BaseController):
    """DiscoveryController controller."""

    id: str = "discovery"

    is_shell: bool = False
    is_listed: bool = True
    is_activatable: bool = True

    resources = ResourceReferences(
        package="yakoon.discovery",
    )

    @property
    def commandsets(self) -> Sequence[type[CommandSet]]:
        """Command sets exported by this controller."""
        return (DiscoveryLookupCommands,)
