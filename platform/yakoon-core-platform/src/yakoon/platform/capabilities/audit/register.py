from yakoon.base.plugins import ModuleExport, ModuleImport, ModuleMeta

meta = ModuleMeta(
    name="yakoon.audit",
    version="0.1.0",
    description="Audit...",
)


def register(ports: ModuleImport) -> ModuleExport:

    return ModuleExport(
        meta,
        app=None,
    )
