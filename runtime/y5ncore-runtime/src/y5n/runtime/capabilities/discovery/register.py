from y5n.base.plugins import ModuleExport, ModuleMeta

meta = ModuleMeta(
    name="y5n.discovery",
    version="0.1.0",
    description="Discovery ...",
)


def register() -> ModuleExport:

    # provide(LookupCandidateStoreService, DefaultLookupCandidateStoreService())
    # provide(LookupParser, DefaultLookupParser())

    # publish(LookupResolver, DefaultLookupResolverService(container))
    # publish(DiscoveryService, discovery)

    return ModuleExport(
        meta,
    )
