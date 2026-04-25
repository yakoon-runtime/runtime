from collections.abc import Sequence

from yakoon.base.plugins import CapabilitySelection, LoadedModule, ModuleImport

from .manager import ModuleManager
from .registry import ModuleRegistry


def load_modules(
    module_import: ModuleImport,
    plugins: list[str],
    capabilities: CapabilitySelection,
) -> Sequence[LoadedModule]:

    modules: list[LoadedModule] = []

    registry = ModuleRegistry()
    manager = ModuleManager(module_import=module_import, on_register=registry.register)

    modules.extend(manager.load_capabilities(capabilities))
    modules.extend(manager.load_modules(plugins))

    return modules
