from yakoon.base.plugins.module import ModuleExport, ModuleMeta
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.shell.controller import ShellCoreController

meta = ModuleMeta(
    name="yakoon.shell",
    version="0.1.0",
    description="Shell ...",
)


def register(services: ServiceDirectory) -> ModuleExport:

    return ModuleExport(
        meta,
        controllers=[
            ShellCoreController,
        ],
    )
