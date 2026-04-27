from yakoon.base.plugins import ModuleExport, ModuleMeta

meta = ModuleMeta(
    name="yakoon.audit",
    version="0.1.0",
    description="Audit...",
)


def register() -> ModuleExport:

    return ModuleExport(
        meta,
        app=None,
    )
