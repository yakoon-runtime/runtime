from yakoon.base.plugins import ModuleExport, ModuleMeta

from .app import ShellApp
from .root import shell

meta = ModuleMeta(
    name="yakoon.shell",
    version="0.1.0",
    description="Shell ...",
)


def register() -> ModuleExport:

    return ModuleExport(
        meta,
        app=ShellApp,
        node=shell,
    )
