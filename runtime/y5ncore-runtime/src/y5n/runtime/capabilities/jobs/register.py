from y5n.base.plugins import ModuleExport, ModuleMeta

meta = ModuleMeta(
    name="y5n.jobs",
    version="0.1.0",
    description="jobs ...",
)


def register() -> ModuleExport:

    return ModuleExport(
        meta,
        app=None,
        # controllers=[JobsController],
    )
