import importlib

from yakoon.base import ports
from yakoon.base.plugins.plugin import LoadedPlugin, PluginExport
from yakoon.base.runtime.services import ServiceDirectory


class PluginManager:

    def __init__(self, root: ServiceDirectory):
        self._root = root
        self._registry = root.get(ports.PluginRegistry)

    def load(self, modules: list[str]) -> list[LoadedPlugin]:
        loaded: list[LoadedPlugin] = []

        for module_name in modules:
            module = importlib.import_module(module_name)

            register_fn = getattr(module, "register", None)
            if not callable(register_fn):
                raise RuntimeError(
                    f"Plugin module '{module_name}' must export a callable register(services) -> PluginExport"
                )

            child = self._root.fork()

            export = register_fn(child)
            if not isinstance(export, PluginExport):
                raise RuntimeError(
                    f"Plugin module '{module_name}' register() must return PluginExport, got {type(export)!r}"
                )

            self._registry.register(export.meta)

            loaded.append(
                LoadedPlugin(
                    export=export,
                    services=child,
                    module_name=module_name,
                )
            )

        return loaded
