from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from yakoon.base.runtime.controllers import Controller, ResourceReferences

from ..commands import DiscoveryLookupCommands

if TYPE_CHECKING:
    from yakoon.base.runtime import CommandSet


class DiscoveryController(Controller):
    """DiscoveryController controller."""

    id: str = "discovery"

    is_shell: bool = False
    is_listed: bool = True
    is_activatable: bool = True

    resources = ResourceReferences(
        package="yakoon.platform.capabilities.discovery",
    )

    @property
    def commandsets(self) -> Sequence[type[CommandSet]]:
        """Command sets exported by this controller."""
        return (DiscoveryLookupCommands,)
