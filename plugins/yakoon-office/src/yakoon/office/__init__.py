from yakoon.base.plugins import ModuleExport, ModuleMeta

meta = ModuleMeta(
    name="yakoon.office",
    version="0.1.0",
    description="Office ...",
)


def register() -> ModuleExport:

    return ModuleExport(
        meta,
        app=None,
        # controllers=[
        #    OfficeMailingCoreController,
        # ],
    )
