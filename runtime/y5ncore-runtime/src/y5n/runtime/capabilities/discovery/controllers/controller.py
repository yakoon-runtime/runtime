from __future__ import annotations

from y5n.base.controllers import Composer, ResourceReferences

from ..commands import DiscoveryLookupCommands


class DiscoveryComposer(Composer):

    command_groups = (DiscoveryLookupCommands,)

    resources = ResourceReferences(
        package="y5n.runtime.capabilities.discovery",
    )
