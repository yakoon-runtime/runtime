from yakoon.base.plugins import ModuleExport, ModuleMeta

from .root import shell

meta = ModuleMeta(
    name="yakoon.shell",
    version="0.1.0",
    description="Shell ...",
)


def register() -> ModuleExport:

    return ModuleExport(
        meta,
        node=shell,
    )
