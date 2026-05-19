from yakoon.base.plugins import ModuleExport, ModuleMeta

from .root import shell


def register() -> ModuleExport:

    return ModuleExport(
        node=shell,
        meta=ModuleMeta(
            name="yakoon.shell",
            version="0.1.0",
            description="Shell ...",
        ),
    )
