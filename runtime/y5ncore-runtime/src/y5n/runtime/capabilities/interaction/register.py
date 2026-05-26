from y5n.base.plugins import ModuleExport, ModuleMeta

meta = ModuleMeta(
    name="y5n.interaction",
    version="0.1.0",
    description="Interaction...",
)


def register() -> ModuleExport:

    # publish(FieldPolicyEngine, DefaultFieldPolicyEngine())

    return ModuleExport(meta)
