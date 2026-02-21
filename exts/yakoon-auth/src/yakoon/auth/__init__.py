from yakoon.auth.controller import AuthCoreController
from yakoon.base.directories.service import ServiceDirectory
from yakoon.base.plugins.plugin import PluginExport, PluginMeta

meta = PluginMeta(
    name="yakoon.auth",
    version="0.1.0",
    description="Auth...",
)


def register(services: ServiceDirectory) -> PluginExport:

    return PluginExport(
        meta,
        controllers=[
            AuthCoreController,
        ],
    )
