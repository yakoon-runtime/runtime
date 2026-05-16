from __future__ import annotations

from yakoon.base.controllers import Composer, ResourceReferences

from ..commands import DiscoveryLookupCommands


class DiscoveryComposer(Composer):

    command_groups = (DiscoveryLookupCommands,)

    resources = ResourceReferences(
        package="yakoon.platform.capabilities.discovery",
    )
