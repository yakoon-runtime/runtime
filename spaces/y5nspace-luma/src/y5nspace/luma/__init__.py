from y5n.api.modules import ModuleExport, ModuleMeta

from .space import luma


def register() -> ModuleExport:
    return ModuleExport(
        node=luma,
        meta=ModuleMeta(
            name="y5n.luma",
            version="0.1.0",
            description="Luma — Spatial Knowledge System",
        ),
    )
