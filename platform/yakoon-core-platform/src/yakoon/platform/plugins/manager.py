import importlib
from typing import Literal, TypeAlias

from yakoon.base.plugins import ModuleRegistry
from yakoon.base.plugins.module import LoadedModule, ModuleExport
from yakoon.base.runtime.services import ServiceDirectory

CapabilityMode: TypeAlias = Literal["default"]
CapabilitySelection: TypeAlias = dict[str, CapabilityMode | None]


class DefaultModuleManager:
    def __init__(
        self,
        root: ServiceDirectory,
        *,
        capability_prefix: str = "yakoon.platform.capabilities",
    ):
        self._root = root
        self._registry = root.get(ModuleRegistry)
        self._capability_prefix = capability_prefix.rstrip(".")

    def load_modules(self, modules: list[str]) -> list[LoadedModule]:
        loaded: list[LoadedModule] = []

        for module_name in modules:
            register_fn = self._resolve_register(module_name)

            child = self._root.fork()

            export = register_fn(child)
            if not isinstance(export, ModuleExport):
                raise RuntimeError(
                    f"Module '{module_name}' register() must return ModuleExport, "
                    f"got {type(export)!r}"
                )

            self._registry.register(export.meta)

            loaded.append(
                LoadedModule(
                    export=export,
                    services=child,
                    module_name=module_name,
                )
            )

        return loaded

    def load_capabilities(
        self,
        capabilities: CapabilitySelection,
    ) -> list[LoadedModule]:
        modules = self.resolve_capability_modules(capabilities)
        return self.load_modules(modules)

    def resolve_capability_modules(
        self,
        capabilities: CapabilitySelection,
    ) -> list[str]:
        modules: list[str] = []

        for name, mode in capabilities.items():
            if mode is None:
                continue

            if mode == "default":
                modules.append(f"{self._capability_prefix}.{name}")
                continue

            raise ValueError(f"Unsupported capability mode for '{name}': {mode!r}")

        return modules

    def _resolve_register(self, module_name: str):
        module = importlib.import_module(module_name)

        register_fn = getattr(module, "register", None)
        if callable(register_fn):
            return register_fn

        try:
            register_module = importlib.import_module(f"{module_name}.register")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                f"Module '{module_name}' must export callable "
                f"register(services) -> ModuleExport either in the package "
                f"or in a 'register' submodule."
            ) from exc

        register_fn = getattr(register_module, "register", None)
        if not callable(register_fn):
            raise RuntimeError(
                f"Module '{module_name}.register' must export callable "
                f"register(services) -> ModuleExport."
            )

        return register_fn
