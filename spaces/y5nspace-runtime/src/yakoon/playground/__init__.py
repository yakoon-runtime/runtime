from y5n.base.plugins import ModuleExport, ModuleMeta

meta = ModuleMeta(
    name="y5n.playground",
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
