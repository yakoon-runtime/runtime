from yakoon.base.plugins import ModuleExport, ModuleImport, ModuleMeta

from .app import DiscoveryApplication

meta = ModuleMeta(
    name="yakoon.discovery",
    version="0.1.0",
    description="Discovery ...",
)


def register(ports: ModuleImport) -> ModuleExport:

    # provide(LookupCandidateStoreService, DefaultLookupCandidateStoreService())
    # provide(LookupParser, DefaultLookupParser())

    # publish(LookupResolver, DefaultLookupResolverService(container))
    # publish(DiscoveryService, discovery)

    return ModuleExport(
        meta,
        app=DiscoveryApplication(platform_ports=ports),
    )
