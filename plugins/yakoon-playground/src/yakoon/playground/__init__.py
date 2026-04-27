from yakoon.base.plugins import ModuleExport, ModuleMeta

meta = ModuleMeta(
    name="yakoon.playground",
    version="0.1.0",
    description="playground ...",
)


def register() -> ModuleExport:

    return ModuleExport(
        meta,
        app=None,
        # controllers=[
        #    DemoControllerDsl,
        #    DemoControllerPatterns,
        # ],
    )
