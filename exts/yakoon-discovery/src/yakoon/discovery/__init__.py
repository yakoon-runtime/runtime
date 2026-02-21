from yakoon.base.directories.service import ServiceDirectory
from yakoon.base.plugins.plugin import PluginExport, PluginMeta
from yakoon.discovery.controller import DiscoveryController
from yakoon.discovery.services.discovery import DiscoveryService
from yakoon.discovery.services.stategies.alias_tag.stategie import (
    LookupAliasTagStrategy,
)

meta = PluginMeta(
    name="yakoon.discovery",
    version="0.1.0",
    description="Capability and intent discovery layer.",
)


def register(services: ServiceDirectory) -> PluginExport:

    discovery = DiscoveryService()
    discovery.register(1, LookupAliasTagStrategy(services))

    return PluginExport(
        meta,
        controllers=[
            DiscoveryController,
        ],
    )
