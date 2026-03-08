from typing import Any

from yakoon.base.capabilities.discovery import (
    DiscoveryService,
    LookupCandidateStoreService,
    LookupParser,
    LookupResolverService,
)
from yakoon.base.plugins import ModuleExport, ModuleMeta
from yakoon.base.runtime.services import ServiceDirectory

from .controllers import DiscoveryController
from .services import (
    DefaultDiscoveryService,
    DefaultLookupCandidateStoreService,
    DefaultLookupParser,
    DefaultLookupResolverService,
    LookupAliasTagStrategy,
)

meta = ModuleMeta(
    name="yakoon.discovery",
    version="0.1.0",
    description="Discovery ...",
)


def register(services: ServiceDirectory) -> ModuleExport:

    public_services: list[type] = []

    discovery = DefaultDiscoveryService()
    discovery.register(1, LookupAliasTagStrategy(services))

    # provide: internal module service (not exported to platform)
    def provide(port_type: type[Any], instance: Any) -> None:
        services.register_static(port_type, instance)

    # publish: public capability port exported to the platform
    def publish(port_type: type, instance: object) -> None:
        provide(port_type, instance)
        public_services.append(port_type)

    provide(LookupCandidateStoreService, DefaultLookupCandidateStoreService())
    provide(LookupParser, DefaultLookupParser())

    publish(LookupResolverService, DefaultLookupResolverService(services))
    publish(DiscoveryService, discovery)

    return ModuleExport(
        meta,
        controllers=[DiscoveryController],
        public_services=public_services,
    )
