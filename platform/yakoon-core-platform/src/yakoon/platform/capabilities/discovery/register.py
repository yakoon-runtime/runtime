from typing import Any

from yakoon.base.capabilities.discovery import (
    DiscoveryService,
    LookupCandidateStoreService,
    LookupParser,
    LookupResolver,
)
from yakoon.base.plugins import ModuleExport, ModuleMeta
from yakoon.base.runtime import Container

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


def register(container: Container) -> ModuleExport:

    public_ports: list[type] = []

    discovery = DefaultDiscoveryService()
    discovery.register(1, LookupAliasTagStrategy(container))

    # provide: internal module service (not exported to platform)
    def provide(port_type: type[Any], instance: Any) -> None:
        container.register_static(port_type, instance)

    # publish: public capability port exported to the platform
    def publish(port_type: type, instance: object) -> None:
        provide(port_type, instance)
        public_ports.append(port_type)

    provide(LookupCandidateStoreService, DefaultLookupCandidateStoreService())
    provide(LookupParser, DefaultLookupParser())

    publish(LookupResolver, DefaultLookupResolverService(container))
    publish(DiscoveryService, discovery)

    return ModuleExport(
        meta,
        controllers=[DiscoveryController],
        public_ports=public_ports,
    )
