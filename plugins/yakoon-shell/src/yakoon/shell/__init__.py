from yakoon.base.plugins import ModuleExport, ModuleImport, ModuleMeta

from .app import ShellApplication

meta = ModuleMeta(
    name="yakoon.shell",
    version="0.1.0",
    description="Shell ...",
)


def register(ports: ModuleImport) -> ModuleExport:

    return ModuleExport(
        meta,
        app=ShellApplication(platform_ports=ports),
    )
