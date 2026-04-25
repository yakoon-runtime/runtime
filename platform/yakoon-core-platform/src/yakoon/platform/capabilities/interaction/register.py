from yakoon.base.plugins import ModuleExport, ModuleImport, ModuleMeta

meta = ModuleMeta(
    name="yakoon.interaction",
    version="0.1.0",
    description="Interaction...",
)


def register(ports: ModuleImport) -> ModuleExport:

    # publish(FieldPolicyEngine, DefaultFieldPolicyEngine())

    return ModuleExport(meta, app=None)
