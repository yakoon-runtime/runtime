from __future__ import annotations

from collections.abc import Sequence

from typing_extensions import Protocol
from y5n.base.plugins import CapabilitySelection, LoadedModule, ModulePorts
from y5n.runtime.plugins import ModuleManager, ModuleRegistry


class SpaceLoader:

    def __init__(
        self,
        spaces: list[str],
        capabilities: CapabilitySelection,
    ):
        self._spaces = spaces
        self._capabilities = capabilities
        self._registry = ModuleRegistry()
        self._manager = ModuleManager(
            on_register=self._registry.register,
        )

    def load(self) -> Sequence[LoadedModule]:
        modules: list[LoadedModule] = []
        modules.extend(self._manager.load_capabilities(self._capabilities))
        modules.extend(self._manager.load_modules(self._spaces))

        return modules


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetImport(Protocol):
    def __call__(self) -> ModulePorts: ...
