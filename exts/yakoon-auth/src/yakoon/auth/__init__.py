from yakoon.auth.controller import AuthCoreController
from yakoon.base.plugins.plugin import PluginExport, PluginMeta
from yakoon.base.runtime.services import ServiceDirectory

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
