from yakoon.base.plugins.plugin import PluginMeta


class DefaultPluginRegistry:
    def __init__(self):
        self._plugins: dict[str, PluginMeta] = {}

    def register(self, meta: PluginMeta) -> None:
        self._plugins[meta.name] = meta

    def list(self) -> list[PluginMeta]:
        return list(self._plugins.values())
