from y5n.base.plugins import ModuleExport, ModuleMeta

from .space import ident


def register() -> ModuleExport:

    return ModuleExport(
        node=ident,
        meta=ModuleMeta(
            name="y5n.ident",
            version="0.1.0",
            description="Identity...",
        ),
    )
