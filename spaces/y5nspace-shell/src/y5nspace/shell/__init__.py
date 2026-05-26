from y5n.api.modules import ModuleExport, ModuleMeta

from .space import shell


def register() -> ModuleExport:

    return ModuleExport(
        node=shell,
        meta=ModuleMeta(
            name="y5n.shell",
            version="0.1.0",
            description="Shell ...",
        ),
    )
