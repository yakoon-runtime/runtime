from typing import Protocol

from .module import ModuleMeta


class ModuleRegistry(Protocol):
    def register(self, meta: ModuleMeta) -> None: ...
    def list(self) -> list[ModuleMeta]: ...
