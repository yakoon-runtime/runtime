from __future__ import annotations

from yakoon.base.controllers import Controller, ResourceReferences

from ..commands import DiscoveryLookupCommands


class DiscoveryController(Controller):
    """DiscoveryController controller."""

    id: str = "discovery"

    commandsets = (DiscoveryLookupCommands,)

    resources = ResourceReferences(
        package="yakoon.platform.capabilities.discovery",
    )
