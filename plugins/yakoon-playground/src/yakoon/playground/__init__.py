from yakoon.base.plugins import ModuleExport, ModuleImport, ModuleMeta

meta = ModuleMeta(
    name="yakoon.playground",
    version="0.1.0",
    description="playground ...",
)


def register(ports: ModuleImport) -> ModuleExport:

    return ModuleExport(
        meta,
        app=None,
        # controllers=[
        #    DemoControllerDsl,
        #    DemoControllerPatterns,
        # ],
    )
