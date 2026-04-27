from __future__ import annotations

from collections.abc import Sequence

from typing_extensions import Protocol

from yakoon.base.plugins import CapabilitySelection, LoadedModule
from yakoon.base.plugins.container import ModulePorts

from .manager import ModuleManager
from .registry import ModuleRegistry


class PluginLoader:

    def __init__(
        self,
        plugins: list[str],
        capabilities: CapabilitySelection,
    ):
        self._plugins = plugins
        self._capabilities = capabilities
        self._registry = ModuleRegistry()
        self._manager = ModuleManager(
            on_register=self._registry.register,
        )

    def load(self) -> Sequence[LoadedModule]:
        modules: list[LoadedModule] = []
        modules.extend(self._manager.load_capabilities(self._capabilities))
        modules.extend(self._manager.load_modules(self._plugins))

        return modules


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetImport(Protocol):
    def __call__(self) -> ModulePorts: ...
