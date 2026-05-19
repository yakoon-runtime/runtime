from yakoon.base.plugins import ModuleExport, ModuleMeta

from .root import ident


def register() -> ModuleExport:

    return ModuleExport(
        node=ident,
        meta=ModuleMeta(
            name="yakoon.ident",
            version="0.1.0",
            description="Identity...",
        ),
    )
