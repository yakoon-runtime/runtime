from yakoon.base.plugins.modules import ModuleMeta


class ModuleRegistry:
    def __init__(self):
        self._plugins: dict[str, ModuleMeta] = {}

    def register(self, meta: ModuleMeta) -> None:
        self._plugins[meta.name] = meta

    def list(self) -> list[ModuleMeta]:
        return list(self._plugins.values())
