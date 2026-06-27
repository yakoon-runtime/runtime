from y5n.api.modules import ModuleExport, ModuleMeta

from .space import crm


def register() -> ModuleExport:
    return ModuleExport(
        node=crm,
        meta=ModuleMeta(
            name="y5n.crm",
            version="0.1.0",
            description="Contact management (Mini CRM)",
        ),
    )
