from yakoon.base import ports as base_ports
from yakoon.base.plugins.plugin import PluginExport, PluginMeta
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.discovery import ports
from yakoon.discovery.controller import DiscoveryController
from yakoon.discovery.services.candidate import LookupCandidateStoreService
from yakoon.discovery.services.discovery import DiscoveryService
from yakoon.discovery.services.lookup import LookupResolverService
from yakoon.discovery.services.stategies.alias_tag.parser import LookupParser
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

    services.register_static(ports.LookupParser, LookupParser())
    services.register_static(ports.DiscoveryService, discovery)
    services.register_static(
        ports.LookupCandidateStoreService, LookupCandidateStoreService()
    )

    services.register_static(
        base_ports.LookupResolverService, LookupResolverService(services)
    )

    return PluginExport(
        meta,
        controllers=[
            DiscoveryController,
        ],
        public_services=[
            ports.DiscoveryService,
            base_ports.LookupResolverService,
        ],
    )
