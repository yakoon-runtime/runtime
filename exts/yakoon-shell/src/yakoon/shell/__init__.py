from yakoon.base.plugins.plugin import PluginExport, PluginMeta
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.shell.controller import ShellCoreController

meta = PluginMeta(
    name="yakoon.shell",
    version="0.1.0",
    description="Shell ...",
)


def register(services: ServiceDirectory) -> PluginExport:

    return PluginExport(
        meta,
        controllers=[
            ShellCoreController,
        ],
    )
