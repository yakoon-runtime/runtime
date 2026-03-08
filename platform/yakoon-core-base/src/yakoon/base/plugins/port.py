from typing import Protocol

from .plugin import PluginMeta


class PluginRegistry(Protocol):
    def register(self, meta: PluginMeta) -> None: ...
    def list(self) -> list[PluginMeta]: ...
