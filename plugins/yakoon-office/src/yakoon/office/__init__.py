from yakoon.base.plugins import ModuleExport, ModuleImport, ModuleMeta

meta = ModuleMeta(
    name="yakoon.office",
    version="0.1.0",
    description="Office ...",
)


def register(ports: ModuleImport) -> ModuleExport:

    return ModuleExport(
        meta,
        app=None,
        # controllers=[
        #    OfficeMailingCoreController,
        # ],
    )
