from __future__ import annotations

from yakoon.base.controllers import Controller, ResourceReferences

from ..commands import DiscoveryLookupCommands


class DiscoveryController(Controller):
    """DiscoveryController controller."""

    id: str = "discovery"

    is_shell: bool = False
    is_listed: bool = True
    is_activatable: bool = True

    commandsets = (DiscoveryLookupCommands,)

    resources = ResourceReferences(
        package="yakoon.platform.capabilities.discovery",
    )
